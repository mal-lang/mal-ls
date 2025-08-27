import typing

import pytest
from tree_sitter import Parser, Tree, TreeCursor

from malls.ts.utils import find_current_scope


@pytest.fixture
def find_current_scope_function_tree(
    utf8_mal_parser: Parser, mal_find_current_scope_function: typing.BinaryIO
) -> Tree:
    return utf8_mal_parser.parse(mal_find_current_scope_function.read())


@pytest.fixture
def find_current_scope_function_cursor(find_current_scope_function_tree: Tree) -> TreeCursor:
    return find_current_scope_function_tree.walk()


parameters = [
    ((4, 0), "category_declaration"),
    ((7, 13), "asset_declaration"),
    ((17, 19), "associations_declaration"),
    ((1, 10), "source_file"),
    ((10, 10), "category_declaration"),
    ((11, 4), "asset_declaration"),
    ((13, 4), "asset_declaration"),
    ((3, 10), "source_file"),
    ((3, 17), "category_declaration"),
    ((15, 4), "source_file"),
    ((18, 0), "associations_declaration"),
]

parameter_ids = [
    "on_space_between_category_and_asset",
    "inside_asset_declaration",
    "inside_association_declaration",
    "outside_all_components",
    "on_name_of_asset",
    "on_bracket_of_asset",
    "on_closing_bracket_of_asset",
    "on_name_of_category",
    "on_bracket_of_category",
    "on_term_association",
    "on_bracket_of_association",
]


@pytest.mark.parametrize("point,expected_node_type", parameters, ids=parameter_ids)
def test_find_current_scope(
    point: (int, int), expected_node_type: str, find_current_scope_function_cursor: TreeCursor
):
    node = find_current_scope(find_current_scope_function_cursor, point)
    assert node.type == expected_node_type
