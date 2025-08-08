import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser
import logging

from malls.ts.utils import visit_expr

log = logging.getLogger(__name__)
MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)


def test_visit_expr_only_collects(mal_visit_expr):
    tree = PARSER.parse(mal_visit_expr.read())
    cursor = tree.walk()

    point = (9, 11)

    while (cursor.node.type != 'asset_expr'): cursor.goto_first_child_for_point(point)

    # we use sets to ensure order does not matter
    cursor.goto_first_child()
    found = []
    visit_expr(cursor, found)

    assert found == [b'a',b'b',b'c']


def test_visit_expr_simple_paranthesized(mal_visit_expr):
    tree = PARSER.parse(mal_visit_expr.read())
    cursor = tree.walk()

    point = (10, 11)

    while (cursor.node.type != 'asset_expr'): cursor.goto_first_child_for_point(point)

    # we use sets to ensure order does not matter
    cursor.goto_first_child()
    found = []
    visit_expr(cursor, found)

    assert found == [b'a',b'z',b'b',b'c']


def test_visit_expr_various_paranthesized(mal_visit_expr):
    tree = PARSER.parse(mal_visit_expr.read())
    cursor = tree.walk()

    point = (11, 11)

    while (cursor.node.type != 'asset_expr'): cursor.goto_first_child_for_point(point)

    # we use sets to ensure order does not matter
    cursor.goto_first_child()
    found = []
    visit_expr(cursor, found)

    assert found == [b'a',b'z',b'b',b'y',b'c',b'f',b'l',b'h',b'n',b'm',b'e',b'x',b'u',b't']


def test_visit_expr_unop(mal_visit_expr):
    tree = PARSER.parse(mal_visit_expr.read())
    cursor = tree.walk()

    point = (12, 11)

    while (cursor.node.type != 'asset_expr'): cursor.goto_first_child_for_point(point)

    # we use sets to ensure order does not matter
    cursor.goto_first_child()
    found = []
    visit_expr(cursor, found)

    assert found == [b'a',b'b',b'c']


def test_visit_expr_single_binop(mal_visit_expr):
    tree = PARSER.parse(mal_visit_expr.read())
    cursor = tree.walk()

    point = (13, 11)

    while (cursor.node.type != 'asset_expr'): cursor.goto_first_child_for_point(point)

    # we use sets to ensure order does not matter
    cursor.goto_first_child()
    found = []
    visit_expr(cursor, found)

    assert found == [b'a',b'b',b'c']


def test_visit_expr_various_binop(mal_visit_expr):
    tree = PARSER.parse(mal_visit_expr.read())
    cursor = tree.walk()

    point = (14, 11)

    while (cursor.node.type != 'asset_expr'): cursor.goto_first_child_for_point(point)

    # we use sets to ensure order does not matter
    cursor.goto_first_child()
    found = []
    visit_expr(cursor, found)

    assert found == [b'a',b'b',b'd',b'e',b'f',b'h',b'i']


def test_visit_expr_single_type(mal_visit_expr):
    tree = PARSER.parse(mal_visit_expr.read())
    cursor = tree.walk()

    point = (15, 11)

    while (cursor.node.type != 'asset_expr'): cursor.goto_first_child_for_point(point)

    # we use sets to ensure order does not matter
    cursor.goto_first_child()
    found = []
    visit_expr(cursor, found)

    assert found == [b'd']


def test_visit_expr_various_type(mal_visit_expr):
    tree = PARSER.parse(mal_visit_expr.read())
    cursor = tree.walk()

    point = (16, 11)

    while (cursor.node.type != 'asset_expr'): cursor.goto_first_child_for_point(point)

    # we use sets to ensure order does not matter
    cursor.goto_first_child()
    found = []
    visit_expr(cursor, found)

    assert found == [b'g',b'h',b'i']


def test_visit_expr_variable(mal_visit_expr):
    tree = PARSER.parse(mal_visit_expr.read())
    cursor = tree.walk()

    point = (17, 11)

    while (cursor.node.type != 'asset_expr'): cursor.goto_first_child_for_point(point)

    # we use sets to ensure order does not matter
    cursor.goto_first_child()
    found = []
    visit_expr(cursor, found)

    assert found == [b'w',b'x',b'y',b'z',b'a']
