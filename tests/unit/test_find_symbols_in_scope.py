import typing

import pytest
import tree_sitter

from malls.ts.utils import find_symbols_in_current_scope


@pytest.fixture
def find_symbols_in_scope_tree(
    utf8_mal_parser: tree_sitter.Parser, mal_find_symbols_in_scope: typing.BinaryIO
) -> tree_sitter.Tree:
    return utf8_mal_parser.parse(mal_find_symbols_in_scope.read())


@pytest.fixture
def find_symbols_in_scope_cursor(
    find_symbols_in_scope_tree: tree_sitter.Tree,
) -> tree_sitter.TreeCursor:
    return find_symbols_in_scope_tree.walk()


# (syntax tree/ts point, expected user symbols, expected keywords)
parameters = [
    ((4, 0), {"Asset1", "Asset2", "Asset3"}, {"extends", "abstract", "asset", "info"}),
    (
        (17, 0),
        {
            "a",
            "c",
            "d",
            "e",
            "L",
            "M",
            "Asset1",
            "Asset2",
        },
        {"info"},
    ),
    ((7, 10), {"var", "c", "compromise", "destroy"}, {"let", "info"}),
    ((13, 10), {"destroy"}, {"info", "let"}),
    ((1, 0), set(), {"category", "associations", "info"}),
]

parameter_ids = [
    "category_scope",
    "association_scope",
    "asset1_scope",
    "asset2_scope",
    "root_node_scope",
]


@pytest.mark.parametrize(
    "point,expected_user_symbols,expected_keywords", parameters, ids=parameter_ids
)
def test_find_symbols(
    point: (int, int),
    expected_user_symbols: set[str],
    expected_keywords: set[str],
    find_symbols_in_scope_cursor: tree_sitter.TreeCursor,
):
    user_symbols, keywords = find_symbols_in_current_scope(find_symbols_in_scope_cursor, point)

    # we use sets to ensure order does not matter
    assert set(user_symbols) == expected_user_symbols
    assert set(keywords) == expected_keywords
