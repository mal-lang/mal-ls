from itertools import chain, repeat

import pytest
from tree_sitter import Parser, TreeCursor

from malls.lsp.classes import Document
from malls.lsp.utils import recursive_parsing
from malls.ts.utils import INCLUDED_FILES_QUERY, find_symbol_definition, run_query

pytest_plugins = ["tests.unit.test_find_symbols_in_scope"]

mal_find_symbols_in_scope_points = zip(
    [
        (3, 12),  # category_declaration
        (11, 10),  # asset declaration, asset name
        (7, 10),  # asset variable
        (8, 10),  # attack step
    ],
    [(3, 0), (11, 4), (7, 6), (8, 8)],
)


@pytest.mark.parametrize("point,expected_result", mal_find_symbols_in_scope_points)
def test_symbol_definition_withouth_building_storage(
    request: pytest.FixtureRequest,
    point: (int, int),
    expected_result: (int, int),
    find_symbols_in_scope_cursor: TreeCursor,
):
    # go to name of category

    # get the node
    cursor = find_symbols_in_scope_cursor
    while cursor.goto_first_child_for_point(point) is not None:
        continue

    # confirm it's an identifier
    assert cursor.node.type == "identifier"

    response = find_symbol_definition(cursor.node, cursor.node.text)

    # ensure position is start of category declaration
    assert response[0].start_point == expected_result


mal_symbol_def_extended_asset_main_points = zip(
    repeat("mal_symbol_def_extended_asset_main"),
    [
        (6, 25),  # asset declaration, extended asset
        (9, 11),
    ],  # variable call
    [(2, 4), (4, 6)],
)
mal_symbol_def_variable_call_extend_chain_main_points = zip(
    repeat("mal_symbol_def_variable_call_extend_chain_main"),
    [(9, 11)],  # variable call, extend chain
    [(5, 6)],
)
symbol_def_variable_declaration_main_points = zip(
    repeat("mal_symbol_def_variable_declaration_main"),
    [
        (10, 20),  # variable declaration
        (17, 21),  # variable declaration, extended asset
        (21, 36),  # variable declaration complex 1
        (22, 36),  # variable declaration complex 2
        (26, 6),  # association asset name 1
        (27, 37),  # association asset name 2
        (28, 12),  # association field name 1
        (28, 32),  # association field name 2
        (30, 22),
    ],  # link name
    [(5, 4), (13, 4), (15, 4), (15, 4), (8, 4), (7, 4), (28, 4), (28, 4), (30, 4)],
)
mal_symbol_def_preconditions_points = zip(
    repeat("mal_symbol_def_preconditions"),
    [
        (11, 15),  # preconditions
        (19, 13),  # preconditions extended asset
        (24, 28),  # preconditions complex 1
        (26, 28),
    ],  # preconditions complex 1
    [(5, 4), (14, 4), (16, 4), (16, 4)],
)
mal_symbol_def_reaches_points = zip(
    repeat("mal_symbol_def_reaches"),
    [
        (13, 22),  # reaches
        (14, 14),
    ],  # reaches single attack step
    [(6, 8), (15, 6)],
)

parameters = chain(
    mal_symbol_def_extended_asset_main_points,
    mal_symbol_def_variable_call_extend_chain_main_points,
    symbol_def_variable_declaration_main_points,
    mal_symbol_def_preconditions_points,
    mal_symbol_def_reaches_points,
)


@pytest.mark.parametrize("fixture_name,point,expected_result", parameters)
def test_symbol_definition_with_storage(
    request: pytest.FixtureRequest,
    utf8_mal_parser: Parser,
    mal_root_str: str,
    fixture_name: str,
    point: (int, int),
    expected_result: (int, int),
):
    # build the storage (mimicks the file parsing in the server)
    storage = {}

    doc_uri = request.getfixturevalue(fixture_name + "_uri")
    file = request.getfixturevalue(fixture_name)
    source_encoded = file.read()
    tree = utf8_mal_parser.parse(source_encoded)

    storage[doc_uri] = Document(tree, source_encoded, doc_uri)

    # obtain the included files
    root_node = tree.root_node

    captures = run_query(root_node, INCLUDED_FILES_QUERY)
    if "file_name" in captures:
        recursive_parsing(mal_root_str, captures["file_name"], storage, doc_uri, [])

    ###################################

    # get the node
    cursor = tree.walk()
    while cursor.goto_first_child_for_point(point) is not None:
        continue

    # confirm it's an identifier
    assert cursor.node.type == "identifier"

    # we use sets to ensure order does not matter
    response = find_symbol_definition(cursor.node, cursor.node.text, doc_uri, storage)

    assert response[0].start_point == expected_result
