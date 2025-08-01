import tree_sitter_mal as ts_mal
from tree_sitter import Language, Node, Point, Query, QueryCursor, TreeCursor

from ..lsp.models import Position

MAL_FILETYPES = (".mal",)
MAL_LANGUAGE = Language(ts_mal.language())

# Pre-made queries
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
            left_field_id: (identifier) @left_field_name
            id: (identifier) @association_name
            right_field_id: (identifier) @right_field_name )
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

    # save the cursor (to have child index)
    cursor = owner.walk()

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

    # obtain owner of the scope
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
