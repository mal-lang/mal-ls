import typing

import pytest
from tree_sitter import Parser

from ..util import server_output

pytest_plugins = ["tests.fixtures.lsp.did_change"]

parameters = [
    ("change_middle_of_file_single_line_client_messages", "mal_change_middle_of_file_single_line"),
    (
        "change_middle_of_file_multiple_lines_client_messages",
        "mal_change_middle_of_file_multiple_lines",
    ),
    ("change_end_of_base_open_notification_client_messages", "mal_change_end_of_file"),
    ("change_middle_of_base_open_twice_client_messages", "mal_change_middle_of_file_twice"),
    ("change_whole_base_open_client_messages", "mal_change_whole_file"),
]
parameter_ids = (args[0] for args in parameters)


@pytest.mark.parametrize(
    "client_messages_fixture_name,expected_file_fixture_name", parameters, ids=parameter_ids
)
def test_changes(
    request: pytest.FixtureRequest,
    utf8_mal_parser: Parser,
    mal_base_open_uri: str,
    client_messages_fixture_name: str,
    expected_file_fixture_name: str,
):
    client_messages: typing.BinaryIO = request.getfixturevalue(client_messages_fixture_name)
    expected_file: typing.BinaryIO = request.getfixturevalue(expected_file_fixture_name)

    new_text = expected_file.read()
    uri = mal_base_open_uri[len("file://") :]

    # send to server
    output, ls, *_ = server_output(client_messages)

    # Ensure LSP stored everything correctly
    assert ls.files[uri].text == new_text
    # we have to parse the file to check if the end result is the same
    tree = utf8_mal_parser.parse(new_text)
    assert str(ls.files[uri].tree.root_node) == str(tree.root_node)

    output.close()
