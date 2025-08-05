import tree_sitter_mal as ts_mal
from tree_sitter import Language, Node, Point, Query, QueryCursor, TreeCursor
import logging

from ..lsp.models import Position

log = logging.getLogger(__name__)
MAL_FILETYPES = (".mal",)
MAL_LANGUAGE = Language(ts_mal.language())

# Pre-made queries

INCLUDED_FILES_QUERY = Query(
    MAL_LANGUAGE,
    """
            (include_declaration
            file: (string) @file_name)
        """,
)


FIND_SYMBOLS_CATEGORY_DECLARATION_QUERY = Query(
    MAL_LANGUAGE,
    """
        (asset_declaration
            ("abstract" @abstract)*
            "asset"
            id: (identifier) @asset_name
            ("extends" (identifier) @extends)*
            ( (meta) @meta)*
        )
        """,
)

FIND_SYMBOLS_ASSOCIATIONS_DECLARATION_QUERY = Query(
    MAL_LANGUAGE,
    """
        (association
            left_id: (identifier) @left_asset
            left_field_id: (identifier) @left_field_name
            id: (identifier) @association_name
            right_field_id: (identifier) @right_field_name )
            right_id: (identifier) @right_asset
            ( (meta) @meta)
        """,
)

FIND_SYMBOLS_ASSET_DECLARATION_QUERY = Query(
    MAL_LANGUAGE,
    """
                [
                    ("let" @var)
                    ((identifier) @symbol)
                    ((meta) @meta)
                ]
            """,
)

FIND_SYMBOLS_ROOT_NODE_QUERY = Query(
    MAL_LANGUAGE,
    """
                [
                    (category_declaration "category" @category (meta)* @meta)
                    ("associations" @associations)
                ]
            """,
)


FIND_EXTENDED_ASSET = Query(
    MAL_LANGUAGE,
    """
        ("extends" (identifier) @identifier_node)
    """
)

FIND_ASSET_DECLARATION = Query(
    MAL_LANGUAGE,
    """
        (asset_declaration 
            "asset"
            (identifier) ) @asset_declaration
    """
)

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
                # we can query to find the position of '{' and check if the position is before or
                # after

                if query_and_compare_scope_pos("asset_declaration", cursor, point):
                    owner = owner.parent
                # no need to go any further, this is the "deepest" possible owner of the scope.
                break
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
    line_utf16 = line_text.encode("utf-16")

    # check for BOM
    bom_size = 0
    if line_utf16.startswith(b"\xff\xfe") or line_utf16.startswith(b"\xfe\xff"):
        bom_size = 2

    # lsp_char * 2 gives us the byte offset in the UTF-16 string
    # UTF-16 chars are 2 bytes long
    # We need to take into account possible BOM
    #
    # lsp_char refers to the position according to the source encoding,
    # decided by the server and client. For now, it is only UTF-16
    utf16_slice = line_utf16[bom_size : bom_size + lsp_char * 2]

    # return to unicode
    string_slice = utf16_slice.decode("utf-16")

    # Encode the string slice to UTF-8 and get its byte length
    byte_offset = len(string_slice.encode("utf-8"))

    return Point(lsp_line, byte_offset)


def find_symbols_category_declaration(owner: Node) -> (dict, dict):
    """
    Given the owner of a scope that is a category declaration, we want to find
    all symbols in this scope. The only possible identifiers correspond to asset
    names, so that is what will be queried
    """

    # query
    captures = run_query(owner, FIND_SYMBOLS_CATEGORY_DECLARATION_QUERY)

    if not captures:  # if nothing was found, then there are no symbols
        return ({}, {})

    user_symbols, keywords = (
        {},
        {"asset": captures["asset_name"][0]},
    )  # otherwise, there are assets defined

    # save defined assets
    for asset_node in captures["asset_name"]:
        user_symbols[asset_node.text.decode()] = asset_node

    # if there are extends, we want to save the extended asset name and keyword
    if "extends" in captures:
        keywords["extends"] = captures["extends"][0]  # we want to store where we found the keyword
        for extends_node in captures["extends"]:
            user_symbols[extends_node.text.decode()] = extends_node

    # include abstract if it exists
    if "abstract" in captures:
        keywords["abstract"] = captures["abstract"][0]

    # include meta if it exists
    if "meta" in captures:
        keywords["info"] = captures["info"][0]

    return (user_symbols, keywords)


def find_symbols_associations_declaration(owner: Node) -> (dict, dict):
    """
    In an associations declaration node, the relevant identifiers are
    field, associations and asset names. However, asset names should
    be queried from categories in the current file and extended files,
    as they are the components where assets are defined. Therefore,
    the only queried things here are association names and field names.
    """

    # query and save the node's text
    captures = run_query(owner, FIND_SYMBOLS_ASSOCIATIONS_DECLARATION_QUERY)

    # add filtered results
    user_symbols = {}
    keywords = {}
    for key in captures:
        if key == "meta":
            keywords["info"] = captures[key][0]
            continue
        for symbol_node in captures[key]:
            user_symbols[symbol_node.text.decode()] = symbol_node

    return (user_symbols, keywords)


def find_symbols_asset_declaration(owner: Node) -> (dict, dict):
    """
    Asset declarations can have many symbols, such as in
    variables, expressions or attack steps. Therefore,
    the easiest method to find them all is querying for
    all identifiers at once
    """

    # Query for identifiers in variable declarations or steps.
    # To avoid including information in the asset declaration
    # (e.g. asset name, extended asset name), we must move
    # the cursor to the child worth querying - asset_definition.
    # If this child exists, it must be the last named child
    # (this is done for efficiency, instead of going to a named child directly)
    user_symbols = {}
    keywords = {}
    if (child := owner.named_children[-1]).type == "asset_definition":
        # If the child exists, query it
        # query and save the node's text
        captures = run_query(child, FIND_SYMBOLS_ASSET_DECLARATION_QUERY)

        # add filtered results
        for key in captures:
            if key == "var":
                keywords["let"] = captures[key]
                continue
            if key == "meta":
                keywords["info"] = captures[key]
                continue
            for symbol_node in captures[key]:
                user_symbols[symbol_node.text.decode()] = symbol_node

    return (user_symbols, keywords)


def find_symbols_root_node(owner: Node) -> (list[str], list[str]):
    """
    Root nodes (source files) do not need to recommend any symbols
    which are user-defined, since there are no variables worth defining
    at this moment. Therefore, the only relevant keywords are the ones
    related to association declaration or category declaration.
    """

    captures = run_query(owner, FIND_SYMBOLS_ROOT_NODE_QUERY)

    keywords = {}
    if "category" in captures:
        keywords["category"] = captures["category"][0]
    if "meta" in captures:
        keywords["info"] = captures["meta"][0]
    if "associations" in captures:
        keywords["associations"] = captures["associations"][0]

    return ({}, keywords)


def find_symbols_in_current_scope(cursor: TreeCursor, point: Point) -> (list[str], list[str]):
    """
    Given a cursor and a point, we want to find all available symbols in
    the current scope. Symbols can refer to identifiers, i.e. user-decided
    strings, that represent components of the language. They can also mean
    keywords in the MAL language, such as `asset` or `extends`

    A list of all symbols is returned.
    """

    # Firstly, obtain the owner of the scope
    owner = find_current_scope(cursor, point)

    match owner.type:
        case "category_declaration":
            return find_symbols_category_declaration(owner)
        case "associations_declaration":
            return find_symbols_associations_declaration(owner)
        case "asset_declaration":
            return find_symbols_asset_declaration(owner)
        case _:  # defaults to root node
            return find_symbols_root_node(owner)


def find_symbols_in_category_hierarchy(owner: Node) -> (dict, dict):
    """
    Given a category declaration, we want to find the symbols in the current scope,
    the children's scope, which are assets, and the parent node (root)
    """

    # symbols and keywords
    symbols = {}
    keywords = {}

    # iterate over the children and get the symbols in the asset declarations, in case there are any
    for child in owner.children:
        if child.type == "asset_declaration":
            child_results_symbols, child_results_keywords = find_symbols_asset_declaration(child)
            # add hierarchy level (-1)
            for child_symbol, child_symbol_node in child_results_symbols.items():
                symbols[child_symbol] = (child_symbol_node, -1)
            for child_keyword, child_keyword_node in child_results_keywords.items():
                keywords[child_keyword] = (child_keyword_node, -1)

    # get the current scope's symbols
    current_results_symbols, current_results_keywords = find_symbols_category_declaration(owner)
    # add hierarchy level (0)
    for current_symbol, current_symbol_node in current_results_symbols.items():
        symbols[current_symbol] = (current_symbol_node, 0)
    for current_keyword, current_keyword_node in current_results_keywords.items():
        keywords[current_keyword] = (current_keyword_node, 0)

    # finally, get the scope for the parent (root node)
    # We need to go to parent twice because direct parent of category is declaration
    parent_results_symbols, parent_results_keywords = find_symbols_root_node(owner.parent.parent)
    # add hierarchy level (1)
    for parent_symbol, parent_symbol_node in parent_results_symbols.items():
        symbols[parent_symbol] = (parent_symbol_node, 1)
    for parent_keyword, parent_keyword_node in parent_results_keywords.items():
        keywords[parent_keyword] = (parent_keyword_node, 1)

    return (symbols, keywords)


def find_symbols_in_association_hierarchy(owner: Node) -> (dict, dict):
    """
    The association does not have any children, so we only have to obtain the current scope's
    symbols and the parent scope's symbols (root node)
    """
    symbols = {}
    keywords = {}

    # get the current scope's symbols
    current_results_symbols, current_results_keywords = find_symbols_associations_declaration(owner)
    # add hierarchy level (0)
    for current_symbol, current_symbol_node in current_results_symbols.items():
        symbols[current_symbol] = (current_symbol_node, 0)
    for current_keyword, current_keyword_node in current_results_keywords.items():
        keywords[current_keyword] = (current_keyword_node, 0)

    # get the parent scope's symbols
    # again, we need to go twice to the parent
    parent_results_symbols, parent_results_keywords = find_symbols_root_node(owner.parent.parent)
    # add hierarchy level (0)
    for parent_symbol, parent_symbol_node in parent_results_symbols.items():
        symbols[parent_symbol] = (parent_symbol_node, 1)
    for parent_keyword, parent_keyword_node in parent_results_keywords.items():
        keywords[parent_keyword] = (parent_keyword_node, 1)

    return symbols, keywords


def find_symbols_in_asset_hierarchy(owner: Node) -> (dict, dict):
    """
    An asset does not have any children, so we only have to return the current scope's,
    parent scope's (category) and parent of parent's (root node) symbols.
    """

    symbols = {}
    keywords = {}

    # get the current scope's symbols
    current_results_symbols, current_results_keywords = find_symbols_asset_declaration(owner)
    # add hierarchy level (0)
    for current_symbol, current_symbol_node in current_results_symbols.items():
        symbols[current_symbol] = (current_symbol_node, 0)
    for current_keyword, current_keyword_node in current_results_keywords.items():
        keywords[current_keyword] = (current_keyword_node, 0)

    # get the parent scope's symbols (category)
    parent_results_symbols, parent_results_keywords = find_symbols_category_declaration(
        owner.parent
    )
    # add hierarchy level (1)
    for parent_symbol, parent_symbol_node in parent_results_symbols.items():
        symbols[parent_symbol] = (parent_symbol_node, 1)
    for parent_keyword, parent_keyword_node in parent_results_keywords.items():
        keywords[parent_keyword] = (parent_keyword_node, 1)

    # get the parent of the parent scope's symbols (root node)
    parent_of_parent_results_symbols, parent_of_parent_results_keywords = find_symbols_root_node(
        owner.parent.parent.parent
    )
    # add hierarchy level (2)
    for (
        parent_of_parent_symbol,
        parent_of_parent_symbol_node,
    ) in parent_of_parent_results_symbols.items():
        symbols[parent_of_parent_symbol] = (parent_of_parent_symbol_node, 2)
    for (
        parent_of_parent_keyword,
        parent_of_parent_keyword_node,
    ) in parent_of_parent_results_keywords.items():
        keywords[parent_of_parent_keyword] = (parent_of_parent_keyword_node, 2)

    return symbols, keywords


def find_children_symbols_for_root_node(owner: Node, symbols: dict, keywords: dict):
    # iterate over categories and associations to get their symbols
    for declaration in owner.children:
        child = declaration.children[0]
        if child.type == "category_declaration":
            # The results come with
            # asset symbols, category symbols, root node symbols
            #
            # Obviously, we only want the first two, as the last corresponds
            # to the current node's symbols
            child_results_symbols, child_results_keywords = find_symbols_in_category_hierarchy(
                child
            )
            # add hierarchy level
            for category_symbol, (category_symbol_node, lvl) in child_results_symbols.items():
                if lvl == -1 or lvl == 0:  # asset symbol, save it as child of child symbol (-2)
                    symbols[category_symbol] = (category_symbol_node, lvl - 1)
                # otherwise it's a root node symbol, which we already have
            for category_keyword, (category_keyword_node, lvl) in child_results_keywords.items():
                if lvl == -1 or lvl == 0:
                    keywords[category_keyword] = (category_keyword_node, lvl - 1)
                # otherwise it's a root node symbol, which we already have
        elif child.type == "associations_declaration":
            # when it comes to associations, we can consider only the symbols in that scope,
            # since associations do not have children
            child_results_symbols, child_results_keywords = find_symbols_associations_declaration(
                child
            )
            # add hierarchy level (-1)
            for current_child_symbol, current_child_symbol_node in child_results_symbols.items():
                symbols[current_child_symbol] = (current_child_symbol_node, -1)
            for current_child_keyword, current_child_keyword_node in child_results_keywords.items():
                keywords[current_child_keyword] = (current_child_keyword_node, -1)


def find_symbols_root_node_hierarchy(owner: Node) -> (dict, dict):
    """
    Root node only has children, so we have to get their symbols. For that, we will
    have to iterate over all categories and get their hierarchy symbols and the
    associations symbols
    """

    symbols = {}
    keywords = {}

    # current node's symbols
    current_results_symbols, current_results_keywords = find_symbols_root_node(owner)
    # add hierarchy level (0)
    for current_symbol, current_symbol_node in current_results_symbols.items():
        symbols[current_symbol] = (current_symbol_node, 0)
    for current_keyword, current_keyword_node in current_results_keywords.items():
        keywords[current_keyword] = (current_keyword_node, 0)

    # get children symbols
    find_children_symbols_for_root_node(owner, symbols, keywords)

    return symbols, keywords


def find_symbols_in_context_hierarchy(cursor: TreeCursor, point: Point) -> (dict, dict):
    """
    This function aims to return the symbols in the hierarchy. This means finding the symbols
    in parents and children.
    """

    # Firstly, obtain the owner of the scope
    owner = find_current_scope(cursor, point)

    match owner.type:
        case "category_declaration":
            return find_symbols_in_category_hierarchy(owner)
        case "associations_declaration":
            return find_symbols_in_association_hierarchy(owner)
        case "asset_declaration":
            return find_symbols_in_asset_hierarchy(owner)
        case _:  # defaults to root node
            return find_symbols_root_node_hierarchy(owner)


def find_symbol_definition_category_declaration(node: Node, symbol: str) -> Point:
    """
    Since we are in a category declaration, the symbol, since it is user-defined,
    must be the category name. So we only need to return the start point of
    the current node.
    """

    return node.start_point

def bfs_search(doc, query, key, symbol, storage):

    def search_match(file, query, nodes, symbol):
        captures = run_query(file.tree.root_node, query)
        if captures:
            nodes = captures[key]
            for node in nodes:
                identifier = node.children_by_field_name("id")
                # if it has identifiers, it must be the first
                if identifier[0].text == symbol:
                    return node
        return None

    # First, check if the asset is defined in the current file
    file = storage[doc]

    if (result:= search_match(file, query, key, symbol)) is not None:
        return result

    # otherwise, we have to check for the included files
    # for that, we will use a BFS (breadth-first search)
    included_files = storage[doc].included_files

    while included_files:
        file = included_files.pop(0)
        if (result := search_match(file, query, key, symbol)) is not None:
            return result
        included_files.extend(storage[file.uri].included_files)

    return None

def find_symbol_definition_asset_declaration(node: Node, symbol: str, document_uri, storage) -> Point:
    """
    Since we are in an asset declaration, the symbol, since it is user-defined,
    can either be the asset name or the extended asset. So we only need to
    check which one it is.
    """

    # find extended asset
    captures = run_query(node,FIND_EXTENDED_ASSET)

    if captures and captures['identifier_node'][0].text==symbol:
        key = 'asset_declaration'
        # in this case, we have to find this asset
        result_node = bfs_search(document_uri, FIND_ASSET_DECLARATION, key, symbol, storage)
        return result_node.start_point if result_node else None
    # we are sure it must be the asset name
    return node.start_point


def find_symbol_definition(node: Node, symbol: str, document_uri: str = None, storage: list = None) -> Point:
    """
    Given a node and a symbol, this function will find the point
    where that symbol is defined.

    Since the node can be of any type, we need to go up the parent
    tree until we find a parent from which we can extract relevant
    information.
    """

    while True:
        match node.type:
            case "category_declaration":
                return find_symbol_definition_category_declaration(node, symbol)
            case "asset_declaration":
                return find_symbol_definition_asset_declaration(node, symbol, document_uri, storage)
            case _:
                node = node.parent  # go to parent if no info proved relevant
        # terminate if there are no more parents
        if node is None:
            return None
