import typing

import pytest
from tree_sitter import Parser, Tree, TreeCursor

from malls.ts.utils import visit_expr


@pytest.fixture
def tree(utf8_mal_parser: Parser, mal_visit_expr: typing.BinaryIO) -> Tree:
    return utf8_mal_parser.parse(mal_visit_expr.read())


@pytest.fixture
def cursor(tree: Tree) -> TreeCursor:
    return tree.walk()


def goto_asset_expression(cursor: TreeCursor, point: (int, int)):
    while cursor.node.type != "asset_expr":
        cursor.goto_first_child_for_point(point)

    cursor.goto_first_child()


point_found_parameters = [
    ((9, 11), [b"a", b"b", b"c"]),
    ((10, 11), [b"a", b"z", b"b", b"c"]),
    (
        (11, 11),
        [
            b"a",
            b"z",
            b"b",
            b"y",
            b"c",
            b"f",
            b"l",
            b"h",
            b"n",
            b"m",
            b"e",
            b"x",
            b"u",
            b"t",
        ],
    ),
    ((12, 11), [b"a", b"b", b"c"]),
    ((13, 11), [b"a", b"b", b"c"]),
    ((14, 11), [b"a", b"b", b"d", b"e", b"f", b"h", b"i"]),
    ((15, 11), [(b"d", "asset")]),
    ((16, 11), [(b"g", "asset"), b"h", b"i"]),
    ((17, 11), [b"w", b"x", b"y", b"z", b"a"]),
]

parameter_names = [
    "only_collects",
    "simple_paranthesized",
    "various_paranthesized",
    "unop",
    "single_binop",
    "various_binop",
    "single_type",
    "various_type",
    "variable",
]


@pytest.mark.parametrize("point,expected", point_found_parameters, ids=parameter_names)
def test_visir_expr(point: (int, int), expected: list[bytes], cursor: TreeCursor):
    goto_asset_expression(cursor, point)
    found = []
    visit_expr(cursor, found)
    assert found == expected
