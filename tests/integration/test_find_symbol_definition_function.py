from pathlib import Path

import pytest
import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser

from malls.lsp.classes import Document
from malls.lsp.utils import recursive_parsing
from malls.ts.utils import INCLUDED_FILES_QUERY, find_symbol_definition, run_query

MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)
FILE_PATH = str(Path(__file__).parent.parent.resolve()) + "/fixtures/mal/"


mal_find_symbols_in_scope_points = [
    ((3, 12), (3, 0)),  # category_declaration
    ((11, 10), (11, 4)),  # asset declaration, asset name
    ((7, 10), (7, 6)),  # asset variable
    ((8, 10), (8, 8)),  # attack step
]


@pytest.mark.parametrize(
    "file_name,point,expected_result",
    [
        ("mal_find_symbols_in_scope", point, expected_result)
        for point, expected_result in mal_find_symbols_in_scope_points
    ],
)
def test_symbol_definition_withouth_building_storage(request, file_name, point, expected_result):
    file = request.getfixturevalue(file_name)
    tree = PARSER.parse(file.read())

    # go to name of category

    # get the node
    cursor = tree.walk()
    while cursor.goto_first_child_for_point(point) is not None:
        continue

    # confirm it's an identifier
    assert cursor.node.type == "identifier"

    response = find_symbol_definition(cursor.node, cursor.node.text)

    # ensure position is start of category declaration
    assert response[0].start_point == expected_result


mal_symbol_def_extended_asset_main_points = [
    ((6, 25), (2, 4)),  # asset declaration, extended asset
    ((9, 11), (4, 6)),  # variable call
]
mal_symbol_def_variable_call_extend_chain_main_points = [
    ((9, 11), (5, 6))  # variable call, extend chain
]
symbol_def_variable_declaration_main_points = [
    ((10, 20), (5, 4)),  # variable declaration
    ((17, 21), (13, 4)),  # variable declaration, extended asset
    ((21, 36), (15, 4)),  # variable declaration complex 1
    ((22, 36), (15, 4)),  # variable declaration complex 2
    ((26, 6), (8, 4)),  # association asset name 1
    ((27, 37), (7, 4)),  # association asset name 2
    ((28, 12), (28, 4)),  # association field name 1
    ((28, 32), (28, 4)),  # association field name 2
    ((30, 22), (30, 4)),  # link name
]
mal_symbol_def_preconditions_points = [
    ((11, 15), (5, 4)),  # preconditions
    ((19, 13), (14, 4)),  # preconditions extended asset
    ((24, 28), (16, 4)),  # preconditions complex 1
    ((26, 28), (16, 4)),  # preconditions complex 1
]
mal_symbol_def_reaches_points = [
    ((13, 22), (6, 8)),  # reaches
    ((14, 14), (15, 6)),  # reaches single attack step
]


@pytest.mark.parametrize(
    "file_name,fixture_name,point,expected_result",
    [
        (
            "symbol_def_extended_asset_main.mal",
            "mal_symbol_def_extended_asset_main",
            point,
            expected_result,
        )
        for point, expected_result in mal_symbol_def_extended_asset_main_points
    ]
    + [
        (
            "symbol_def_variable_call_extend_chain_main.mal",
            "mal_symbol_def_variable_call_extend_chain_main",
            point,
            expected_result,
        )
        for point, expected_result in mal_symbol_def_variable_call_extend_chain_main_points
    ]
    + [
        (
            "symbol_def_variable_declaration_main.mal",
            "mal_symbol_def_variable_declaration_main",
            point,
            expected_result,
        )
        for point, expected_result in symbol_def_variable_declaration_main_points
    ]
    + [
        ("symbol_def_preconditions.mal", "mal_symbol_def_preconditions", point, expected_result)
        for point, expected_result in mal_symbol_def_preconditions_points
    ]
    + [
        ("symbol_def_reaches.mal", "mal_symbol_def_reaches", point, expected_result)
        for point, expected_result in mal_symbol_def_reaches_points
    ],
)
def test_symbol_definition_with_storage(
    request,
    file_name,
    fixture_name,
    point,
    expected_result,
):
    # build the storage (mimicks the file parsing in the server)
    storage = {}

    doc_uri = FILE_PATH + file_name
    file = request.getfixturevalue(fixture_name)
    source_encoded = file.read()
    tree = PARSER.parse(source_encoded)

    storage[doc_uri] = Document(tree, source_encoded, doc_uri)

    # obtain the included files
    root_node = tree.root_node

    captures = run_query(root_node, INCLUDED_FILES_QUERY)
    if "file_name" in captures:
        recursive_parsing(FILE_PATH, captures["file_name"], storage, doc_uri, [])

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
