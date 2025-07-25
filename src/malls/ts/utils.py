from tree_sitter import *
import tree_sitter_mal as ts_mal

import tree_sitter_mal as ts_mal

MAL_FILETYPES = (".mal",)
MAL_LANGUAGE = Language(ts_mal.language())

def run_query(node: Node, query: Query):
    query_cursor = QueryCursor(query)
    captures = query_cursor.captures(node)
    return captures

def compare_points(pointA: Point, pointB: Point):
    '''
    Check if pointA is after pointB
    '''
    start_x = pointA[0]
    start_y = pointA[1]
    # starts in another row
    if (start_x > pointB[0] or  
        (start_x==pointB[0] and start_y > pointB[1])): # same row but bigger column
                return True
    return False

def query_and_compare_scope_pos(query_node_type: str, cursor: TreeCursor, point: Point) -> bool:
    '''
    This function will query for '{' (beginning of the scope) and return if the given point
    happens before or after the location of the '{'
    '''

    query = Query(MAL_LANGUAGE,"""
    ("""+query_node_type+"""
        "{" @scope_beginning )
    """)

    start_point = run_query(cursor.node, query)['scope_beginning'][0].start_point
    return compare_points(start_point,point)

def find_current_scope(cursor: TreeCursor, point: Point):
    '''
    Given a cursor and a document position, return the node that
    "owns" the scope. Scopes are separated by curly brackets - {}

    The only components with brackets are categories, assets and
    associations. So, the "owner" of the scope has to be one of
    these kinds, or the root node, if the position falls outside all of them
    '''

    owner, root_node = cursor.node, cursor.node 

    while (cursor.goto_first_child_for_point(point) != None):

        # `goto_first_child_for_point` gives the first child containing the point
        # or that starts after the point, so we must ensure we did not
        # skip the point, i.e. we are still in range
        if (compare_points(cursor.node.range.start_point, point)):
            break

        match cursor.node.type:
            case "category_declaration":
                # we have to check if the point is before or after the '{'
                # we can use query to find this
                owner = cursor.node

                if (query_and_compare_scope_pos('category_declaration',cursor,point)):
                    owner = root_node
                    break
            case "asset_declaration":
                owner = cursor.node
                # but first, we need to know if the child is before or after the '{'.
                # we can query to find the position of '{' and check if the position is before or after

                if (query_and_compare_scope_pos('asset_declaration',cursor,point)):
                    owner = owner.parent
                break # no need to go any further, this is the "deepest" possible owner of the scope.
            case "associations_declaration":
                owner = cursor.node

                # also need to know if the node is before or after '{'
                if (query_and_compare_scope_pos('associations_declaration',cursor,point)):
                    owner = root_node
                break
            case _:
                pass

    return owner

def lsp_to_tree_sitter(text: str, lsp_line: int, lsp_char: int) -> Point:
    """
    Converts an LSP position (UTF-16 character index) to a Tree-sitter position (UTF-8 byte offset).
    """
    lines = text.splitlines(keepends=True)
    
    # Get correct line
    line_text = lines[lsp_line]
    
    # Convert to UTF-16 little endian (each UTF-16 code unit is 2 bytes)
    line_utf16 = line_text.encode('utf-16-le')
    
    # lsp_char * 2 gives us the byte offset in the UTF-16 string
    utf16_slice = line_utf16[:lsp_char * 2]
    
    # return to unicode
    string_slice = utf16_slice.decode('utf-16-le')
    
    # Encode the string slice to UTF-8 and get its byte length
    byte_offset = len(string_slice.encode('utf-8'))
    
    return Point(lsp_line, byte_offset)
