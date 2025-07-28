from ..lsp.models import Position
from tree_sitter import Point
import tree_sitter_mal as ts_mal
from tree_sitter import Language, Node, Point, Query, QueryCursor, TreeCursor

MAL_FILETYPES = (".mal",)
MAL_LANGUAGE = Language(ts_mal.language())


def run_query(node: Node, query: Query):
    query_cursor = QueryCursor(query)
    captures = query_cursor.captures(node)
    return captures

def compare_points(pointA: Point, pointB: Point):
    """
    Check if pointA is after pointB
    """
    start_x = pointA[0]
    start_y = pointA[1]
    # starts in another row
    if start_x > pointB[0] or (
        start_x == pointB[0] and start_y > pointB[1]
    ):  # same row but bigger column
        return True
    return False

def query_and_compare_scope_pos(query_node_type: str, cursor: TreeCursor, point: Point) -> bool:
    """
    This function will query for '{' (beginning of the scope) and return if the given point
    happens before or after the location of the '{'
    """

    query = Query(
        MAL_LANGUAGE,
        """
    ("""
        + query_node_type
        + """
        "{" @scope_beginning )
    """,
    )

    start_point = run_query(cursor.node, query)["scope_beginning"][0].start_point
    return compare_points(start_point, point)

def find_current_scope(cursor: TreeCursor, point: Point):
    """
    Given a cursor and a document position, return the node that
    "owns" the scope. Scopes are separated by curly brackets - {}

    The only components with brackets are categories, assets and
    associations. So, the "owner" of the scope has to be one of
    these kinds, or the root node, if the position falls outside all of them
    """

    owner, root_node = cursor.node, cursor.node

    while cursor.goto_first_child_for_point(point) is not None:
        # `goto_first_child_for_point` gives the first child containing the point
        # or that starts after the point, so we must ensure we did not
        # skip the point, i.e. we are still in range
        if compare_points(cursor.node.range.start_point, point):
            break

        match cursor.node.type:
            case "category_declaration":
                # we have to check if the point is before or after the '{'
                # we can use query to find this
                owner = cursor.node

                if query_and_compare_scope_pos("category_declaration", cursor, point):
                    owner = root_node
                    break
            case "asset_declaration":
                owner = cursor.node
                # but first, we need to know if the child is before or after the '{'.
                # we can query to find the position of '{' and check if the position is before or after

                if query_and_compare_scope_pos("asset_declaration", cursor, point):
                    owner = owner.parent
                break  # no need to go any further, this is the "deepest" possible owner of the scope.
            case "associations_declaration":
                owner = cursor.node

                # also need to know if the node is before or after '{'
                if query_and_compare_scope_pos("associations_declaration", cursor, point):
                    owner = root_node
                break
            case _:
                pass

    return owner

def lsp_to_tree_sitter_position(text: str, pos: Position) -> Point:
    """
    Converts an LSP position (UTF-16 character index) to a Tree-sitter position (UTF-8 byte offset).
    """
    lsp_line, lsp_char = pos.line, pos.character
    
    lines = text.splitlines(keepends=True)
    
    # Get correct line
    line_text = lines[lsp_line]
    
    # The idea is to conver the string to UTF-16.
    # Since UTF-16 characters correspond to 2 bytes,
    # if we multiply the character position by 2
    # and then encode back to UTF-8, we effectively
    # cut back to the byte number

    # Convert to UTF-16 (each UTF-16 code unit is 2 bytes)
    # https://en.wikipedia.org/wiki/UTF-16#Byte-order_encoding_schemes
    line_utf16 = line_text.encode('utf-16')

    # check for BOM
    bom_size = 0
    if line_utf16.startswith(b'\xff\xfe') or line_utf16.startswith(b'\xfe\xff'):
        bom_size = 2
    
    # lsp_char * 2 gives us the byte offset in the UTF-16 string
    # UTF-16 chars are 2 bytes long
    # We need to take into account possible BOM
    #
    # lsp_char refers to the position according to the source encoding,
    # decided by the server and client. For now, it is only UTF-16
    utf16_slice = line_utf16[bom_size:bom_size + lsp_char * 2]
    
    # return to unicode
    string_slice = utf16_slice.decode('utf-16')
    
    # Encode the string slice to UTF-8 and get its byte length
    byte_offset = len(string_slice.encode('utf-8'))
    
    return Point(lsp_line, byte_offset)

def find_symbols_category_declaration(owner: Node) -> list[str]:
    '''
    Given the owner of a scope that is a category declaration, we want to find
    all symbols in this scope. The only possible identifiers correspond to asset
    names, so that is what will be queried
    '''

    query = Query(
        MAL_LANGUAGE, 
        """
        (asset_declaration
            id: (identifier) @asset_name )
        """)

    # query and save the node's text
    results = [asset_name.text.decode() for asset_name in run_query(owner, query)['asset_name']]

    # also include relevant keywords in the category scope
    results.extend([
        'abstract',
        'extends',
        'asset',
        'info', # for metas
    ])

    # filter out repeated symbols (e.g. assets with the same name)
    final_result = []
    [final_result.append(x) for x in results if x not in final_result]

    return final_result

def find_symbols_associations_declaration(owner: Node) -> list[str]:
    '''
    In an associations declaration node, the relevant identifiers are
    field, associations and asset names. However, asset names should
    be queried from categories in the current file and extended files,
    as they are the components where assets are defined. Therefore,
    the only queried things here are association names and field names.
    '''

    query = Query(
        MAL_LANGUAGE, 
        """
        (association
            left_field_id: (identifier) @left_field_name
            id: (identifier) @association_name
            right_field_id: (identifier) @right_field_name )
        """)

    # query and save the node's text
    captures = run_query(owner, query)

    # add filtered results
    results = []
    for key in captures:
        for symbol in captures[key]:
            symbol = symbol.text.decode()
            if symbol not in results: results.append(symbol)

    # also include relevant keywords in the category scope (only meta)
    results.append(
        'info', # for metas
    )

    return results

def find_symbols_asset_declaration(owner: Node) -> list[str]:
    '''
    Asset declarations can have many symbols, such as in
    variables, expressions or attack steps. Therefore,
    the easiest method to find them all is querying for
    all identifiers at once
    '''

    # Query for identifiers in variable declarations or steps.
    # To avoid including information in the asset declaration
    # (e.g. asset name, extended asset name), we must move
    # the cursor to the child worth querying - asset_definition.
    # If this child exists, it must be the last named child
    # (this is done for efficiency, instead of going to a named child directly)
    if ((child := owner.named_children[-1]).type=='asset_definition'):
        # If the child exists, query it
        query = Query(
            MAL_LANGUAGE, 
            """
            (
                (identifier) @symbol)
            """)

        # query and save the node's text
        captures = run_query(child, query)

        # add filtered results
        results = []
        for key in captures:
            for symbol in captures[key]:
                symbol = symbol.text.decode()
                if symbol not in results: results.append(symbol)

    # also include relevant keywords in the category scope
    # TODO should we recommend probability distributions (TTC)?
    results.extend([
        'let', # for variables
        'info', # for metas
    ])

    return results

def find_symbols_root_node(owner: Node) -> list[str]:
    '''
    Root nodes (source files) do not need to recommend any symbols
    which are user-defined, since there are no variables worth defining
    at this moment. Therefore, the only relevant keywords are the ones
    related to association declaration or category declaration.
    '''
    return [
        'category',
        'info',
        'associations',
    ]

def find_symbols_in_current_scope(cursor: TreeCursor, point: Point) -> list[str]:
    '''
    Given a cursor and a point, we want to find all available symbols in
    the current scope. Symbols can refer to identifiers, i.e. user-decided
    strings, that represent components of the language. They can also mean
    keywords in the MAL language, such as `asset` or `extends`

    A list of all symbols is returned.
    '''

    # obtain owner of the scope
    if not owner:
        owner = find_current_scope(cursor, point)

    match owner.type:
        case 'category_declaration':
            return find_symbols_category_declaration(owner)
        case 'associations_declaration':
            return find_symbols_associations_declaration(owner)
        case 'asset_declaration':
            return find_symbols_asset_declaration(owner)
        case _: # defaults to root node
            return find_symbols_root_node(owner)

def find_symbols_in_category_hierarchy(owner: Node) -> list[tuple[int,list[str]]]:
    '''
    Given a category declaration, we want to find the symbols in the current scope,
    the children's scope, which are assets, and the parent node (root)
    '''

    # keep track of used symbols (e.g. avoid repeated 'info')
    used_symbols = []

    # iterate over the children and get the symbols in the asset declarations, in case there are any
    child_symbols = []
    for child in owner.children:
        if child.type == 'asset_declaration':
            child_symbols.extend(find_symbols_asset_declaration(child))

    used_symbols = list(set(child_symbols)) # use set to remove duplicates
    child_scope = (-1,used_symbols)

    # get the current scope's symbols
    current_symbols = find_symbols_category_declaration(owner)
    # remove already considered symbols
    current_symbols_filtered = list(set(current_symbols) - set(used_symbols))
    current_scope = (0,current_symbols_filtered)

    # finally, get the scope for the parent (root node)
    parent_symbols = find_symbols_root_node(owner.parent)
    # remove used symbols
    parent_symbols_filtered = list(set(parent_symbols) - set(used_symbols))
    parent_scope = (1, parent_symbols_filtered)
    
    return [child_scope, current_scope, parent_scope]

def find_symbols_in_association_hierarchy(owner: Node) -> list[tuple[int,list[str]]]:
    '''
    The association does not have any children, so we only have to obtain the current scope's
    symbols and the parent scope's symbols (root node)
    '''
    used_symbols = []

    # get the current scope's symbols
    used_symbols = find_symbols_associations_declaration(owner)
    current_scope = (0,used_symbols)

    # get the parent scope's symbols
    parent_symbols = find_symbols_root_node(owner.parent)
    # remove already considered symbols
    parent_symbols_filtered = list(set(parent_symbols) - set(used_symbols))
    parent_scope = (1,parent_symbols_filtered)

    return [current_scope, parent_scope]

def find_symbols_in_asset_hierarchy(owner: Node) -> list[tuple[int,list[str]]]:
    '''
    An asset does not have any children, so we only have to return the current scope's,
    parent scope's (category) and parent of parent's (root node) symbols.
    '''

    used_symbols = []

    # get the current scope's symbols
    used_symbols = find_symbols_asset_declaration(owner)
    current_scope = (0,used_symbols)

    # get the parent scope's symbols (category)
    parent_symbols = find_symbols_category_declaration(owner.parent)
    # remove already considered symbols
    parent_symbols_filtered = list(set(parent_symbols) - set(used_symbols))
    parent_scope = (1,parent_symbols_filtered)

    # get the parent of the parent scope's symbols (root node)
    parent_of_parent_symbols = find_symbols_root_node(owner.parent.parent)
    # remove already considered symbols
    parent_of_parent_symbols_filtered = list(set(parent_of_parent_symbols) - set(used_symbols))
    parent_of_parent_scope = (2,parent_of_parent_symbols_filtered)

    return [current_scope, parent_scope, parent_of_parent_scope]

def find_symbols_root_node_hierarchy(owner: Node) -> list[tuple[int,list[str]]]:
    '''
    Root node only has children, so we have to get their symbols. For that, we will
    have to iterate over all categories and get their hierarchy symbols and the 
    associations symbols
    '''

    # current node's symbols
    used_symbols = find_symbols_root_node(owner)
    current_scope = (0,used_symbols)

    # iterate over categories and associations to get their symbols
    child_symbols = []
    child_of_child_symbols = []
    for child in owner.children:
        if child.type == 'category_declaration':
            # The results come in the following order:
            # asset symbols, category symbols, root node symbols
            #
            # Obviously, we only want the first two, as the last corresponds
            # to the current node's symbols
            current_child_symbols, current_child_of_child_symbols, _ = find_symbols_in_category_hierarchy(child)
            # remove repeated and save them
            child_symbols.extend(list(set(current_child_symbols) - set(child_symbols)))
            child_of_child_symbols.extend(list(set(current_child_of_child_symbols) - set(child_of_child_symbols)))
        elif child.type == 'associations_declaration':
            # when it comes to associations, we can consider only the symbols in that scope,
            # since associations do not have children
            current_child_symbols = find_symbols_associations_declaration(child)
            # remove repeated and save
            child_symbols.extend(list(set(current_child_symbols) - set(child_symbols)))

    child_scope = (-1,child_symbols)
    child_of_child_scope = (-2,child_of_child_symbols)

    return [child_of_child_scope, child_scope, current_scope]

def find_symbols_in_context_hiearchy(cursor: TreeCursor, point: Point) -> list[tuple[int,str]]:
    '''
    This function aims to return the symbols in the hierarchy. This means finding the symbols
    in parents and children.
    '''

    # Firstly, obtain the owner of the scope
    owner = find_current_scope(cursor, point)

    match owner.type:
        case 'find_symbols_in_category_hierarchy':
            return find_symbols_in_category_hierarchy(owner)
        case 'find_symbols_in_association_hierarchy':
            return find_symbols_in_association_hierarchy(owner)
        case 'find_symbols_in_asset_hierarchy':
            return find_symbols_in_asset_hierarchy(owner)
        case _: # defaults to root node
            return find_symbols_root_node_hierarchy(owner)

