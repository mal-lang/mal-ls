import itertools
import typing

import pytest

from ..fixtures.lsp.goto_definition import FixtureCallback
from ..util import get_lsp_json, server_output

pytest_plugins = ["tests.fixtures.lsp.goto_definition"]

# Test parameters
mal_find_symbols_in_scope_points = zip(
    [
        (3, 12),  # category_declaration, "goto_def_1"
        (11, 10),  # asset declaration, asset name, "goto_def_2"
        (7, 10),  # asset variable, "goto_def_3"
        (8, 10),  # attack step, "goto_def_4"
    ],
    itertools.repeat("find_symbols_in_scope"),
)
mal_symbol_def_extended_asset_main_points = zip(
    [
        (6, 25),  # asset declaration, extended asset, "goto_def_5"
        (9, 11),  # variable call, "goto_def_6"
    ],
    itertools.repeat("symbol_def_extended_asset_main"),
)
mal_symbol_def_variable_call_extend_chain_main_points = zip(
    [
        (9, 11)  # variable call, extend chain, "goto_def_7"
    ],
    itertools.repeat("symbol_def_variable_call_extend_chain_main"),
)
symbol_def_variable_declaration_main_points = zip(
    [
        (10, 20),  # variable declaration, "goto_def_8"
        (17, 21),  # variable declaration, extended asset, "goto_def_9"
        (21, 36),  # variable declaration complex 1, "goto_def_10"
        (22, 36),  # variable declaration complex 2, "goto_def_11"
        (26, 6),  # association asset name 1, "goto_def_12"
        (27, 37),  # association asset name 2, "goto_def_13"
        (28, 12),  # association field name 1, "goto_def_14"
        (28, 32),  # association field name 2, "goto_def_15"
        (30, 22),  # link name, "goto_def_16"
    ],
    itertools.repeat("symbol_def_variable_declaration_main"),
)
mal_symbol_def_preconditions_points = zip(
    [
        (11, 15),  # preconditions, "goto_def_17"
        (19, 13),  # preconditions extended asset, "goto_def_18"
        (24, 28),  # preconditions complex 1, "goto_def_19"
        (26, 28),  # preconditions complex 1, "goto_def_20"
    ],
    itertools.repeat("symbol_def_preconditions"),
)
# this one is specifically list so that the last case can be reused in
# test_goto_definition_wrong_symbol
mal_symbol_def_reaches_points = list(
    zip(
        [
            (13, 22),  # reaches, "goto_def_21"
            (14, 14),  # reaches single attack step, "goto_def_22"
            (10, 7),  # random non-user defined symbol, "goto_def_23"
        ],
        itertools.repeat("symbol_def_reaches"),
    )
)


goto_input_location_and_files = itertools.chain(
    mal_find_symbols_in_scope_points,
    mal_symbol_def_extended_asset_main_points,
    mal_symbol_def_variable_call_extend_chain_main_points,
    symbol_def_variable_declaration_main_points,
    mal_symbol_def_preconditions_points,
    mal_symbol_def_reaches_points,
)

goto_expected_location_and_files = [
    ((3, 0), "find_symbols_in_scope"),  # "goto_def_1"
    ((11, 4), "find_symbols_in_scope"),  # "goto_def_2"
    ((7, 6), "find_symbols_in_scope"),  # "goto_def_3"
    ((8, 8), "find_symbols_in_scope"),  # "goto_def_4"
    ((2, 4), "symbol_def_extended_asset_aux3"),  # "goto_def_5"
    ((4, 6), "symbol_def_extended_asset_aux3"),  # "goto_def_6"
    ((5, 6), "symbol_def_variable_call_extend_chain_aux2"),  # "goto_def_7"
    ((5, 4), "symbol_def_variable_declaration_main"),  # "goto_def_8"
    ((13, 4), "symbol_def_variable_declaration_main"),  # "goto_def_9"
    ((15, 4), "symbol_def_variable_declaration_main"),  # "goto_def_10"
    ((15, 4), "symbol_def_variable_declaration_main"),  # "goto_def_11"
    ((8, 4), "symbol_def_variable_declaration_main"),  # "goto_def_12"
    ((7, 4), "symbol_def_variable_declaration_main"),  # "goto_def_13"
    ((28, 4), "symbol_def_variable_declaration_main"),  # "goto_def_14"
    ((28, 4), "symbol_def_variable_declaration_main"),  # "goto_def_15"
    ((30, 4), "symbol_def_variable_declaration_main"),  # "goto_def_16"
    ((5, 4), "symbol_def_preconditions"),  # "goto_def_17"
    ((14, 4), "symbol_def_preconditions"),  # "goto_def_18"
    ((16, 4), "symbol_def_preconditions"),  # "goto_def_19"
    ((16, 4), "symbol_def_preconditions"),  # "goto_def_20"
    ((6, 8), "symbol_def_reaches"),  # "goto_def_21"
    ((15, 6), "symbol_def_reaches"),  # "goto_def_22"
]

# [((input location, input file), (expected location, expected file))]
find_symbols_in_scope_expected_results = list(
    zip(goto_input_location_and_files, goto_expected_location_and_files)
)


def parameter_id(argvalue: (((int, int), str), ((int, int), str))) -> object:
    # Turns the combination of test parameters of find_symbols_in_scope_expected_results
    # into more legigble/simpler/useful names
    inputs, outputs = argvalue
    (origin_line, origin_char), origin_file = inputs
    (expected_line, expected_char), expected_file = outputs
    return (
        f"{origin_file}:L{origin_line},C{origin_char}"
        "-"
        f"{expected_file}:L{expected_line},C{expected_char}"
    )


# Tests
@pytest.mark.parametrize(
    "inputs,expected_outputs",
    find_symbols_in_scope_expected_results,
    ids=map(parameter_id, find_symbols_in_scope_expected_results),
)
def test_goto_definition(
    request: pytest.FixtureRequest,
    inputs: ((int, int), str),
    expected_outputs: ((int, int), str),
    goto_definition_client_messages: FixtureCallback[typing.BinaryIO],
):
    origin_location, origin_file = inputs
    expected_point, expected_file = expected_outputs

    expected_file_uri = request.getfixturevalue(f"mal_{expected_file}_uri")

    uri_fixture = request.getfixturevalue(f"mal_{origin_file}_uri")
    file_fixture = request.getfixturevalue(f"mal_{origin_file}")
    fixture = goto_definition_client_messages(uri_fixture, file_fixture, origin_location)

    output, ls, *_ = server_output(fixture)

    output.seek(0)
    response = get_lsp_json(output)
    response = get_lsp_json(output)

    start_point_dict = response["result"]["range"]["start"]
    start_point = (start_point_dict["line"], start_point_dict["character"])
    file = response["result"]["uri"]

    assert start_point == expected_point
    assert file == expected_file_uri

    output.close()


def test_goto_definition_wrong_symbol(
    request: pytest.FixtureRequest,
    goto_definition_client_messages: FixtureCallback[typing.BinaryIO],
):
    """
    This test aims to check that the LS can handle
    requests for symbols which are not user-defined
    """
    # previously known as goto_def_23
    inputs = next(itertools.islice(mal_symbol_def_reaches_points, 2, 3))

    origin_location, origin_file = inputs

    uri_fixture = request.getfixturevalue(f"mal_{origin_file}_uri")
    file_fixture = request.getfixturevalue(f"mal_{origin_file}")
    fixture = goto_definition_client_messages(uri_fixture, file_fixture, origin_location)

    # send to server
    output, ls, *_ = server_output(fixture)

    output.seek(0)
    response = get_lsp_json(output)
    response = get_lsp_json(output)

    result = response["result"]

    assert result is None

    output.close()
