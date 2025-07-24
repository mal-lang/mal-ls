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

    
