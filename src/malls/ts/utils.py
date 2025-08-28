import copy
import logging

import tree_sitter_mal as ts_mal
from tree_sitter import Language, Node, Point, Query, QueryCursor, Tree, TreeCursor

from ..lsp.enums import DiagnosticSeverity
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
    """,
)

FIND_ASSET_DECLARATION = Query(
    MAL_LANGUAGE,
    """
        (asset_declaration
            "asset"
            (identifier) ) @asset_declaration
    """,
)

FIND_PERIOD = Query(
    MAL_LANGUAGE,
    """
        ("." @period_node)
    """,
)


ERRORS_QUERY = Query(
    MAL_LANGUAGE,
    """
    [
        ((ERROR) @error-node)
        ((MISSING) @missing-node)
    ]
    """,
)


COMMENTS_QUERY = Query(
    MAL_LANGUAGE,
    """
    ((comment) @comment_node)*
    """,
)


def find_variable_query(variable_name: str):
    query = Query(
        MAL_LANGUAGE,
        """
            (asset_variable
                "let"
                id: (identifier) @var_identifier
        """
        + f'(#eq? @var_identifier "{variable_name.decode()}") ) @variable_declaration',
    )
    return query


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


def find_current_scope(cursor: TreeCursor, point: Point) -> Node:
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


def lsp_to_tree_sitter_position(text: str, pos: Position, new_text: str = None) -> Point:
    """
    Converts an LSP position (UTF-16 character index) to a Tree-sitter position (UTF-8 byte offset).
    """
    lsp_line, lsp_char = pos.line, pos.character

    lines = text.splitlines(keepends=True)

    if lsp_line >= len(lines):
        # there is an extension to the text itself (didChange)
        # so we have to consider the line being written
        line_text = new_text.splitlines(keepends=True)[lsp_line - len(lines)]
    else:
        # Get correct line
        line_text = lines[lsp_line]

    # The idea is to conver the string to UTF-16.
    # Since UTF-16 characters correspond to 2 bytes,
    # if we multiply the character position by 2
    # and then encode back to UTF-8, we effectively
    # cut back to the byte number

    # Convert to UTF-16 (each UTF-16 code unit is 2 bytes)
    # https://en.wikipedia.org/wiki/UTF-16#Byte-order_encoding_schemes
    line_utf16 = line_text.decode().encode("utf-16")

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


def tree_sitter_to_lsp_position(text: str, pos: Point, new_text: str = None) -> Position:
    """
    Converts a Tree-sitter position (UTF-8 byte offset) to an LSP position (UTF-16 character index).
    """
    ts_line, ts_byte_offset = pos.row, pos.column

    lines = text.splitlines(keepends=True)

    if len(lines) > ts_line:
        line_text = lines[ts_line]

        # Decode the line text from UTF-8 to a string
        line_string = line_text.decode("utf-8")

        # Get the slice of the string up to the byte offset
        string_slice = line_string.encode("utf-8")[:ts_byte_offset].decode("utf-8")

        # The length of this slice in UTF-16 code units is the LSP character position
        lsp_char = len(string_slice.encode("utf-16-le")) // 2
    else:
        lsp_char = 0

    return Position(line=ts_line, character=lsp_char)


def find_symbols_category_declaration(owner: Node) -> (dict, dict):
    """
    Given the owner of a scope that is a category declaration, we want to find
    all symbols in this scope. The only possible identifiers correspond to asset
    names, so that is what will be queried
    """

    # query
    captures = run_query(owner, FIND_SYMBOLS_CATEGORY_DECLARATION_QUERY)

    if not captures:  # if nothing was found, then there are no symbols
        return ({}, {"asset": {}, "extends": {}, "abstract": {}, "info": {}})

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
    else:
        keywords["extends"] = {}

    # include abstract if it exists
    if "abstract" in captures:
        keywords["abstract"] = captures["abstract"][0]
    else:
        keywords["abstract"] = {}

    # include meta if it exists
    if "meta" in captures:
        keywords["info"] = captures["info"][0]
    else:
        keywords["info"] = {}

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
    else:
        return ({}, {"info": {}, "let": {}})

    if "let" not in keywords:
        keywords["let"] = {}
    if "info" not in keywords:
        keywords["info"] = {}
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
    else:
        keywords["category"] = {}
    if "meta" in captures:
        keywords["info"] = captures["meta"][0]
    else:
        keywords["info"] = {}
    if "associations" in captures:
        keywords["associations"] = captures["associations"][0]
    else:
        keywords["associations"] = {}

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

    return node


def bfs_search(doc: str, query: Query, key: str, symbol: str, storage: dict):
    """
    The objective of this function is to find a given symbol in the file
    hierarchy. Since a file might include others, we will query all files
    in a breadth-first search (BFS) manner until we find the symbol we want.

    In this scenario, `doc` refers to the starting file, from which we will
    traverse the included files. The `query` is what we will be searching for
    in each while, and the `key` is what must be in the capture in case there
    is a possible match. Since many matches can be retrieved given a query,
    we will try to find which one matches the `symbol` (done in `search_match()`).
    Finally, to traverse the included files, we will use the `storage`, which
    is where all files are saved.

    For more information on the algoritm:
    https://en.wikipedia.org/wiki/Breadth-first_search
    """

    def search_match(file, query, nodes, symbol):
        captures = run_query(file.tree.root_node, query)
        if captures:
            nodes = captures[key]
            for node in nodes:
                identifier = node.children_by_field_name("id")
                # if it has identifiers, it must be the first
                if not symbol or identifier[0].text == symbol:
                    return node
        return None

    # First, check if the item is defined in the current file
    file = storage[doc]

    if (result := search_match(file, query, key, symbol)) is not None:
        return (result, file)

    # otherwise, we have to check for the included files
    # for that, we will use a BFS (breadth-first search)
    included_files = copy.copy(storage[doc].included_files)

    while included_files:
        file = included_files.pop(0)
        if (result := search_match(file, query, key, symbol)) is not None:
            return (result, file)
        included_files.extend(copy.copy(storage[file.uri].included_files))

    return (None, file)


def find_symbol_definition_asset_declaration(
    node: Node, symbol: str, document_uri, storage
) -> Point:
    """
    Since we are in an asset declaration, the symbol, since it is user-defined,
    can either be the asset name or the extended asset. So we only need to
    check which one it is.
    """

    # find extended asset
    captures = run_query(node, FIND_EXTENDED_ASSET)

    if captures and captures["identifier_node"][0].text == symbol:
        key = "asset_declaration"
        # in this case, we have to find this asset
        result_node, result_file = bfs_search(
            document_uri, FIND_ASSET_DECLARATION, key, symbol, storage
        )
        return result_node, result_file.uri
    # we are sure it must be the asset name
    return node, document_uri


def find_symbol_definition_variable_declaration(node: Node, symbol: str):
    """
    Since we are in a variable declaration, the only relevant symbol has
    to be the variable name itself, so we just need to return the current
    node's position
    """

    return node


def find_symbol_definition_attack_step_declaration(node: Node, symbol: str):
    """
    Since we are in an attack step declaration, the only relevant symbol has
    to be the attack step's name itself, so we just need to return the current
    node's position
    """

    return node


def find_symbol_definition_variable_substitution(
    node: Node, symbol: str, document_uri: str, storage: dict
):
    """
    Since we are in a variable substitution, we need to find where the
    variable is defined. This means querying this asset, its parent if
    there is one, and so on.
    """

    # first, we need to go to the asset itself
    while node.type != "asset_declaration":
        node = node.parent

    # start by querying the current file
    captures = run_query(node, find_variable_query(symbol))

    # if the query returns something, we found the variable in
    # the current file
    if captures:
        return (captures["variable_declaration"][0], document_uri)

    # otherwise, we have to up the hierarchy (extended assets)
    # to try and find one where the variable is defined
    while True:
        captures = run_query(node, FIND_EXTENDED_ASSET)

        # if no included node, stop
        if not captures:
            return (None, document_uri)

        # otherwise, try to find the extended asset
        extended_asset_name = captures["identifier_node"][0].text
        results = bfs_search(
            document_uri, FIND_ASSET_DECLARATION, "asset_declaration", extended_asset_name, storage
        )

        # extended asset not found
        if not results:
            return (None, document_uri)

        # update node and file
        node, file = results
        document_uri = file.uri

        if captures := run_query(node, find_variable_query(symbol)):
            return (captures["variable_declaration"][0], document_uri)


def visit_expr(cursor, found, document_uri: str = None, storage: dict = None):
    r"""
    Given a complex expression, this function will be able to partition it
    and return a list with only the relevant component of each set. For instance,
    A.(B \/ C).D.G would return [A,B,D,G] to facilitate following the chain of
    associations.
    """

    if cursor.node.type == "identifier":
        found.append(cursor.node.text)
    elif cursor.node.text == b"(":
        cursor.goto_next_sibling()
        visit_expr(cursor, found, document_uri, storage)
        cursor.goto_next_sibling()
    elif cursor.node.type == "asset_variable_substitution":
        # get where the variable is referenced
        var_node, _ = find_symbol_definition_variable_substitution(
            cursor.node, cursor.node.children_by_field_name("id")[0].text, document_uri, storage
        )
        # visit the variable definition
        var_cursor = var_node.walk()
        var_cursor.goto_first_child()
        var_cursor.goto_next_sibling()  # skip 'let'
        var_cursor.goto_next_sibling()  # skip name of var
        var_cursor.goto_next_sibling()  # skip '='
        var_cursor.goto_first_child()  # visit the definition
        visit_expr(var_cursor, found, document_uri, storage)
    else:
        match cursor.node.type:
            case "asset_expr_binop":
                if cursor.node.children_by_field_name("operator")[0].text == b".":
                    cursor.goto_first_child()
                    visit_expr(cursor, found, document_uri, storage)
                    cursor.goto_next_sibling()  # ignore operator
                    cursor.goto_next_sibling()
                    visit_expr(cursor, found, document_uri, storage)
                    cursor.goto_parent()
                else:
                    # in other operators these assets have a common ancestor,
                    # so we can just return one of them and, when we search for
                    # the association recursively, we will eventually find
                    # the association
                    cursor.goto_first_child()
                    visit_expr(cursor, found, document_uri, storage)
                    cursor.goto_parent()
            case "asset_expr_unop":
                cursor.goto_first_child()
                visit_expr(cursor, found, document_uri, storage)
                cursor.goto_parent()
            case "asset_expr_type":
                # a type is simply mentioning a "subasset", i.e.
                # if we have a[b] then there is an asset b that extends a.
                # This simplifies the process quite a lot, since we don't
                # really need to know what comes before, only the symbol 'b'
                found.clear()
                found.append((cursor.node.children_by_field_name("type_id")[0].text, "asset"))


def find_asset_from_association(
    node: Node, asset_name: str, field_name: str, document_uri: str, storage: dict
):
    # build query to find association where the field name corresponds to our search
    query = Query(
        MAL_LANGUAGE,
        f"""
    [
        (association
            left_id: (identifier) @asset_id
            right_field_id: (identifier) @field_id
            (#eq? @asset_id "{asset_name.decode()}")
            (#eq? @field_id "{field_name.decode()}")
        )
        (association
            left_field_id: (identifier) @field_id
            right_id: (identifier) @asset_id
            (#eq? @asset_id "{asset_name.decode()}")
            (#eq? @field_id "{field_name.decode()}")
        )
    ] @association
    """,
    )

    # find association
    result_node, result_file = bfs_search(document_uri, query, "association", None, storage)

    # if the association is not found, it possibly was defined in an extended asset,
    # so we have to try and find it higher up in the hierarchy
    if not result_node:
        captures = run_query(node, FIND_EXTENDED_ASSET)
        if not captures:
            return (None, document_uri)
        extended_asset_name = captures["identifier_node"][0].text
        result, _ = bfs_search(
            document_uri, FIND_ASSET_DECLARATION, "asset_declaration", extended_asset_name, storage
        )
        return find_asset_from_association(
            result, extended_asset_name, field_name, document_uri, storage
        )

    # return node
    if result_node.children_by_field_name("left_id")[0].text == asset_name:
        result_point, result_file = bfs_search(
            document_uri,
            FIND_ASSET_DECLARATION,
            "asset_declaration",
            result_node.children_by_field_name("right_id")[0].text,
            storage,
        )
        return result_point, result_file.uri
    else:
        result_point, result_file = bfs_search(
            document_uri,
            FIND_ASSET_DECLARATION,
            "asset_declaration",
            result_node.children_by_field_name("left_id")[0].text,
            storage,
        )
        return result_point, result_file.uri


def find_asset_from_expr(node: Node, symbol: str, document_uri: str, storage: dict, assets: list):
    """
    The objective of this function is to find the node where an asset
    is defined.

    We will start by obtaining a list that is the breakdown of the association chain.
    From that, we will follow the associations until we reach the one where the chosen
    symbol is located.
    """

    # 1st we get the list of relevant components of the expr.
    # This will make it easier to follow the chain of expressions
    if not assets:
        assets = []
        visit_expr(node.children[0].walk(), assets, document_uri, storage)

    # with this list we can easily follow the chain of associations.
    # We start with the current asset and find an association that contains
    # the first element of the list. We go to that Asset. Then repeat, for
    # the second element in the list. And so on

    # get asset name
    while node.type != "asset_declaration":
        node = node.parent
    asset_name = node.children_by_field_name("id")[0].text

    # This loop will start by retrieving the first field form the list and find an association
    # where the current asset mentions this field. From that association we get the asset name
    # of the field. If the field corresponds to what the user was searching for, we need to find
    # where the asset was declared and return it. Otherwise, we need to continue down the chain
    # of associations
    while assets:
        el = assets.pop(0)
        el_name = el
        # if we have a tuple, then we have to find the asset directly, not from the association
        if type(el) is tuple:
            el_name = el[0]
            node, file = bfs_search(
                document_uri, FIND_ASSET_DECLARATION, "asset_declaration", el_name, storage
            )
        else:
            # retrieve name of asset
            node, file = find_asset_from_association(node, asset_name, el, document_uri, storage)
        if not node:
            break
        asset_name = node.children_by_field_name("id")[0].text
        if el_name == symbol:
            if type(el) is tuple:
                result = node
            else:
                result, file = bfs_search(
                    document_uri, FIND_ASSET_DECLARATION, "asset_declaration", asset_name, storage
                )
            return (result, file.uri)
    return (None, document_uri)


def find_symbol_reaching(
    node: Node, symbol: str, pos: (Point, Point), document_uri: str, storage: dict
):
    """
    Since we are in a binop expression, we need to determine if
    the node is an attack step or a field
    """

    # first check the parent
    if node.parent.type in ("asset_variable", "preconditions"):
        # if it's a variable or a precondition, we are certainly
        # talking about fields and only need to find the association
        # where they are defined
        result = find_asset_from_expr(node, symbol, document_uri, storage, [])
        return result

    # otherwise, it's either a field or an attack step
    # query the node to see if there is a `.` following the start_point
    query_cursor = QueryCursor(FIND_PERIOD)
    query_cursor.set_point_range(pos[0], node.end_point)
    captures = query_cursor.captures(node)

    # if there are captures, then we know there is a period `.`
    # after our symbol, so it's a field
    if captures:
        # find a field
        result = find_asset_from_expr(node, symbol, document_uri, storage, [])
        return result
    else:
        # otherwise, it's an attack step
        assets = []
        visit_expr(node.children[0].walk(), assets, document_uri, storage)
        assets.pop(-1)  # remove last element (which is the attack step)
        # get the asset where the attack step is defined (last element)
        if assets:  # go down the chain
            asset_name = assets[-1]
            if type(assets[-1]) is tuple:
                asset_name = asset_name[0]
            asset, result_file = find_asset_from_expr(
                node, asset_name, document_uri, storage, assets
            )
        else:
            asset = node.parent.parent.parent  # go to asset
            result_file = document_uri
        # and finally find the attack step declaration
        query = Query(
            MAL_LANGUAGE,
            f"""
            (attack_step
                id: (identifier) @name
                (#eq? @name "{symbol.decode()}")
            ) @attack_step
            """,
        )
        if captures := run_query(asset, query):
            node = captures["attack_step"][0]
            return (node, result_file)
        return (None, document_uri)


def find_symbol_definition_association(
    node: Node, symbol: str, document_uri: str, storage: dict
) -> Point:
    """
    In an association, if the symbol corresponds to either the right or left asset, we have
    to find where that asset is defined. Otherwise, we simply need to return the current node,
    as that is where the association name and fields are defined.
    """
    if symbol in (
        node.child_by_field_name("left_id").text,
        node.child_by_field_name("right_id").text,
    ):
        key = "asset_declaration"
        # in this case, we have to find this asset
        result_node, result_file = bfs_search(
            document_uri, FIND_ASSET_DECLARATION, key, symbol, storage
        )
        return (result_node, result_file.uri) if result_node else (None, document_uri)
    else:
        return (node, document_uri)


def find_symbol_definition(
    node: Node, symbol: str, document_uri: str = None, storage: list = None
) -> (Node, str):
    """
    Given a node and a symbol, this function will find the point
    where that symbol is defined.

    Since the node can be of any type, we need to go up the parent
    tree until we find a parent from which we can extract relevant
    information.
    """

    original_position = (node.start_point, node.end_point)

    while True:
        match node.type:
            case "category_declaration":
                return (find_symbol_definition_category_declaration(node, symbol), document_uri)
            case "asset_declaration":
                return find_symbol_definition_asset_declaration(node, symbol, document_uri, storage)
            case "asset_variable":
                return (find_symbol_definition_variable_declaration(node, symbol), document_uri)
            case "attack_step":
                return (find_symbol_definition_attack_step_declaration(node, symbol), document_uri)
            case "asset_variable_substitution":
                return find_symbol_definition_variable_substitution(
                    node, symbol, document_uri, storage
                )
            case "asset_expr":
                return find_symbol_reaching(node, symbol, original_position, document_uri, storage)
            case "association":
                return find_symbol_definition_association(node, symbol, document_uri, storage)
            case _:
                node = node.parent  # go to parent if no info proved relevant
        # terminate if there are no more parents
        if node is None:
            return (None, document_uri)


def position_to_node(tree: Tree, text: str, position: Position):
    """
    Given a tree and an LSP position, this function will obtain the innermost
    node in that position
    """

    # convert position
    point = lsp_to_tree_sitter_position(text, position)
    cursor = tree.walk()
    while cursor.goto_first_child_for_point(point) is not None:
        continue
    return (cursor.node, point, cursor.node.text)


def build_diagnostic(node: Node, text: str, error: bool) -> dict:
    """
    Helper function to build a dictionary corresponding to a diagonstic,
    so it can be sent to the Client as is
    """
    # start by converting the position
    start_position = tree_sitter_to_lsp_position(text, node.start_point)
    end_position = tree_sitter_to_lsp_position(text, node.end_point)

    # TODO find better messages and information about error/missing nodes
    return {
        "range": {
            "start": {"line": start_position.line, "character": start_position.character},
            "end": {"line": end_position.line, "character": end_position.character},
        },
        "severity": DiagnosticSeverity.Error if error else DiagnosticSeverity.Warning,
        "message": "Node not recongized" if error else "Node missing",
    }


def query_for_error_nodes(tree: Tree, text: str, doc_uri: str, notification_storage: dict):
    """
    This function will find all error/missing nodes and save the diagnostic
    in case any problem is found
    """

    # Find all error/missing nodes
    captures = run_query(tree.root_node, ERRORS_QUERY)

    # clear old captures
    if doc_uri in notification_storage:
        notification_storage[doc_uri] = []
    if "error-node" in captures:
        for error_node in captures["error-node"]:
            diagnostic = build_diagnostic(error_node, text, True)
            if doc_uri in notification_storage:
                notification_storage[doc_uri].append(diagnostic)
            else:
                notification_storage[doc_uri] = [diagnostic]
    if "missing-node" in captures:
        for missing_node in captures["missing-node"]:
            diagnostic = build_diagnostic(missing_node, text, False)
            if doc_uri in notification_storage:
                notification_storage[doc_uri].append(diagnostic)
            else:
                notification_storage[doc_uri] = [diagnostic]

    return


def find_meta_comment_category_declaration(node: Node) -> list:
    """
    In a category declaration, we will try to find if the node has
    any meta information and, if so, return it.
    """
    meta_info = []
    for children in node.children_by_field_name("meta"):
        meta_info.append(children)

    return meta_info


def find_meta_comment_asset_declaration(node: Node) -> list:
    """
    In an asset declaration, we will try to find if the node has
    any meta information and, if so, return it.
    """
    meta_info = []
    for children in node.children_by_field_name("meta"):
        meta_info.append(children)

    return meta_info


def find_meta_comment_attack_step(node: Node) -> list:
    """
    In an attack step, we will try to find if the node has
    any meta information and, if so, return it.
    """
    meta_info = []
    for children in node.children_by_field_name("meta"):
        meta_info.append(children)

    return meta_info


def find_meta_comment_asset_variable(
    node: Node, symbol: str, document_uri: str, storage: dict
) -> list:
    """
    In an asset variable, we will follow the expression
    chain and get the asset where the symbol is defined.
    Once we have it, we just have to obtain the meta
    comments it contains
    """
    asset, _ = find_asset_from_expr(
        node.child_by_field_name("value"), symbol, document_uri, storage, []
    )

    if not asset:
        return []

    meta_info = []
    for children in asset.children_by_field_name("meta"):
        meta_info.append(children)

    return meta_info


def find_meta_comment_asset_variable_subsitution(
    node: Node, symbol: str, document_uri: str, storage: dict
) -> list:
    """
    In an asset variable substition, we will have to first find
    where the variable is defined. Afterwards, follow the expression
    chain and get the asset referenced by the variable. Once we have
    it, we just have to obtain the meta comments it contains.
    """

    # find where the variable is defined
    variable_node, _ = find_symbol_definition_variable_substitution(
        node, symbol, document_uri, storage
    )

    if variable_node is None:
        # in case the variable is not defined anywhere
        return []

    # divide the expression
    assets = []
    visit_expr(variable_node.children[-1].children[0].walk(), assets, document_uri, storage)

    # obtain the last expression component (so we find the asset referenced by the variable)
    asset_symbol = assets[-1]

    # find the asset the variable refers to
    asset, _ = find_asset_from_expr(
        variable_node.child_by_field_name("value"), asset_symbol, document_uri, storage, assets
    )

    if not asset:
        # in case the asset is not found
        return []

    # otherwise get the meta corresponding to that asset
    meta_info = []
    for children in asset.children_by_field_name("meta"):
        meta_info.append(children)

    return meta_info


def find_meta_comment_asset_expr(
    node: Node, symbol: str, document_uri: str, storage: dict, pos: tuple
) -> list:
    """
    In an asset expr, we can simply find where the asset mentioned by the symbol is defined
    (via the expression chain) and find the needed meta comments.
    """

    # find asset from expression
    asset, _ = find_symbol_reaching(node, symbol, pos, document_uri, storage)

    if not asset:
        # in case the asset is not found
        return []

    # otherwise get the meta corresponding to that asset
    meta_info = []
    for children in asset.children_by_field_name("meta"):
        meta_info.append(children)

    return meta_info


def find_meta_comment_association(
    node: Node, symbol: str, document_uri: str, storage: dict
) -> list:
    """
    In an association, we can call the auxiliary `find_symbol_definition_association`
    which will find the asset referenced by the symbol or the current node otherwise,
    from which we can find the corresponding meta.
    """

    # find the node where the meta is defined (either the current node or an asset node)
    result_node, _ = find_symbol_definition_association(node, symbol, document_uri, storage)

    if not result_node:
        # in case the asset is not found
        return []

    # otherwise get the meta corresponding to that asset
    meta_info = []
    for children in result_node.children_by_field_name("meta"):
        meta_info.append(children)

    return meta_info


def find_meta_comment_function(
    node: Node, symbol: str, document_uri: str = None, storage: dict = None
) -> list:
    """
    Given a node and a symbol, this function will find the point
    where that symbol is defined.

    Since the node can be of any type, we need to go up the parent
    tree until we find a parent from which we can extract relevant
    information.
    """

    original_position = (node.start_point, node.end_point)

    while True:
        match node.type:
            case "category_declaration":
                return find_meta_comment_category_declaration(node)
            case "asset_declaration":
                return find_meta_comment_asset_declaration(node)
            case "attack_step":
                return find_meta_comment_attack_step(node)
            case "asset_variable":
                return find_meta_comment_asset_variable(node, symbol, document_uri, storage)
            case "asset_variable_substitution":
                return find_meta_comment_asset_variable_subsitution(
                    node, symbol, document_uri, storage
                )
            case "asset_expr":
                return find_meta_comment_asset_expr(
                    node, symbol, document_uri, storage, original_position
                )
            case "association":
                return find_meta_comment_association(node, symbol, document_uri, storage)
            case _:
                node = node.parent  # go to parent if no info proved relevant
        # terminate if there are no more parents
        if node is None:
            return []


def find_comments_function(
    node: Node, symbol: str, document_uri: str = "", storage: dict = {}
) -> list:
    """
    Given a node and a symbol, this function will find the comments
    associated to that symbol. Comments are considered to be associated
    with a symbol if they appear in consecutive lines above the symbol.

    E.g.:
        // but not this

        // this as well
        // this comment is connected
        let myVar = ...
        // technically this *could* be connected to above but its a potentially complex scenario
        // so only count it towards the node below, if there is one


    The easiest way to do this is to find all comments in the file and only keep those
    which appear in consecutive lines above the symbol.
    """

    start_row = node.start_point.row

    # find comments
    captures = run_query(storage[document_uri].tree.root_node, COMMENTS_QUERY)
    if not captures:
        return []  # there are no comments

    # sort captures by row
    sorted_comments = sorted(
        filter(lambda item: item.start_point.row < start_row, captures["comment_node"]),
        key=lambda item: item.start_point.row,
    )

    comments = [sorted_comments[0]]
    previous_row = sorted_comments[0].end_point.row

    for comment_node in sorted_comments[1:]:
        current_row = comment_node.start_point.row

        # if the comment is in a consecutive row,
        # we keep it
        if current_row == previous_row + 1:
            comments.append(comment_node)
            previous_row = current_row  # update row
        else:
            # otherwise, restart the count
            comments = [comment_node]
            previous_row = comment_node.end_point.row

    return comments if previous_row == start_row - 1 else []
