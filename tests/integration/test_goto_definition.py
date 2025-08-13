import logging
from pathlib import Path

import pytest
import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser

from ..util import get_lsp_json, server_output

log = logging.getLogger(__name__)
MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)
FILE_PATH = str(Path(__file__).parent.parent.resolve()) + "/fixtures/mal/"

simplified_file_path = FILE_PATH + "main.mal"


def filepath_to_uri(filepath: str) -> str:
    """
    Converts a native filesystem path to a file:// URI.
    """
    path_obj = Path(filepath)

    absolute_path_obj = path_obj.resolve()

    return absolute_path_obj.as_uri()


find_symbols_in_scope_expected_results = [
    ("goto_def_1", (3, 0), "find_symbols_in_scope"),
    ("goto_def_2", (11, 4), "find_symbols_in_scope"),
    ("goto_def_3", (7, 6), "find_symbols_in_scope"),
    ("goto_def_4", (8, 8), "find_symbols_in_scope"),
    ("goto_def_5", (2, 4), "symbol_def_extended_asset_aux3"),
    ("goto_def_6", (4, 6), "symbol_def_extended_asset_aux3"),
    ("goto_def_7", (5, 6), "symbol_def_variable_call_extend_chain_aux2"),
    ("goto_def_8", (5, 4), "symbol_def_variable_declaration_main"),
    ("goto_def_9", (13, 4), "symbol_def_variable_declaration_main"),
    ("goto_def_10", (15, 4), "symbol_def_variable_declaration_main"),
    ("goto_def_11", (15, 4), "symbol_def_variable_declaration_main"),
    ("goto_def_12", (8, 4), "symbol_def_variable_declaration_main"),
    ("goto_def_13", (7, 4), "symbol_def_variable_declaration_main"),
    ("goto_def_14", (28, 4), "symbol_def_variable_declaration_main"),
    ("goto_def_15", (28, 4), "symbol_def_variable_declaration_main"),
    ("goto_def_16", (30, 4), "symbol_def_variable_declaration_main"),
    ("goto_def_17", (5, 4), "symbol_def_preconditions"),
    ("goto_def_18", (14, 4), "symbol_def_preconditions"),
    ("goto_def_19", (16, 4), "symbol_def_preconditions"),
    ("goto_def_20", (16, 4), "symbol_def_preconditions"),
    ("goto_def_21", (6, 8), "symbol_def_reaches"),
    ("goto_def_22", (15, 6), "symbol_def_reaches"),
]


@pytest.mark.parametrize(
    "fixture_name,expected_point,expected_file",
    [
        (fixture_name, point, file)
        for fixture_name, point, file in find_symbols_in_scope_expected_results
    ],
)
def test_goto_definition(request, fixture_name, expected_point, expected_file):
    # send to server
    fixture = request.getfixturevalue(fixture_name)
    output, ls, *_ = server_output(fixture)

    output.seek(0)
    response = get_lsp_json(output)
    response = get_lsp_json(output)

    start_point_dict = response["result"]["range"]["start"]
    start_point = (start_point_dict["line"], start_point_dict["character"])
    file = response["result"]["uri"]

    assert start_point == expected_point
    assert file == filepath_to_uri(FILE_PATH + expected_file + ".mal")

    output.close()


def test_goto_definition_wrong_symbol(goto_def_23):
    """
    This test aims to check that the LS can handle
    requests for symbols which are not user-defined
    """
    # send to server
    output, ls, *_ = server_output(goto_def_23)

    output.seek(0)
    response = get_lsp_json(output)
    response = get_lsp_json(output)

    result = response["result"]

    assert result is None

    output.close()
