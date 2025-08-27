import io
import typing
from pathlib import Path

import pytest
import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser

from ..util import build_rpc_message_stream, get_lsp_json, server_output

pytest_plugins = ["tests.fixtures.lsp.conftest"]

MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)
FILE_PATH = str(Path(__file__).parent.parent.resolve()) + "/fixtures/mal/"

simplified_file_path = FILE_PATH + "main.mal"

symbols_in_category_hierarchy = [
    "Asset1",
    "Asset2",
    "Asset3",
    "extends",
    "abstract",
    "asset",
    "info",
]
symbols_in_associations_hierarchy = [
    "a",
    "c",
    "d",
    "e",
    "L",
    "M",
    "Asset1",
    "Asset2",
]
symbols_in_asset1_hierarchy = [
    "var",
    "c",
    "compromise",
    "destroy",
    "let",
    "info",
]
symbols_in_asset2_hierarchy = [
    "destroy",
    "let",
    "info",
]
symbols_in_root_node_hierarchy = [
    "info",
    "category",
    "associations",
]

parameters = [
    ((0, 4), symbols_in_category_hierarchy),
    ((0, 18), symbols_in_associations_hierarchy),
    ((0, 7), symbols_in_asset1_hierarchy),
    ((0, 13), symbols_in_asset2_hierarchy),
    ((0, 0), symbols_in_root_node_hierarchy),
]
parameter_names = [
    "symbols_in_category_hierarchy",
    "symbols_in_associations_hierarchy",
    "symbols_in_asset1_hierarchy",
    "symbols_in_asset2_hierarchy",
    "symbols_in_root_node_hierarchy",
]

pytest_plugins = ["tests.fixtures.mal"]


@pytest.fixture
def open_completion_document_notification(
    client_notifications: list[dict],
    client_messages: list[dict],
    mal_completion_document: io.BytesIO,
    mal_completion_document_uri: str,
) -> dict:
    """
    Sends a didOpen notification bound to the MAL fixture file completion_document.
    """
    message = {
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": mal_completion_document_uri,
                "languageId": "mal",
                "version": 0,
                "text": mal_completion_document.read().decode("utf8"),
            }
        },
    }
    client_notifications.append(message)
    client_messages.append(message)
    return message


@pytest.fixture
def completion_request(
    client_requests: list[dict], client_messages: list[dict], mal_completion_document_uri: str
) -> typing.Callable[[(int, int)], dict]:
    def make(position: (int, int)):
        character, line = position
        message = {
            "id": len(client_requests),
            "jsonrpc": "2.0",
            "method": "textDocument/completion",
            "params": {
                "textDocument": {
                    "uri": mal_completion_document_uri,  # find_symbols_in_scope_path
                },
                "position": {
                    "line": line,
                    "character": character,
                },
            },
        }
        client_requests.append(message)
        client_messages.append(message)
        return message

    return make


@pytest.fixture
def completion_client_messages(
    client_messages: list[dict],
    initalize_request,
    initalized_notification,
    open_completion_document_notification,
    completion_request: typing.Callable[[(int, int)], dict],
) -> typing.Callable[[(int, int)], io.BytesIO]:  # noqa: E501
    def make(position: (int, int)) -> io.BytesIO:
        completion_request(position)
        return build_rpc_message_stream(client_messages)

    return make


@pytest.mark.parametrize("location,completion_list", parameters, ids=parameter_names)
def test_completion(
    location: (int, int),
    completion_list: list[str],
    completion_client_messages: typing.Callable[[(int, int)], io.BytesIO],
):
    # send to server
    fixture = completion_client_messages(location)
    output, ls, *_ = server_output(fixture)

    output.seek(0)
    response = get_lsp_json(output)
    response = get_lsp_json(output)

    returned_completion_list = [completion["label"] for completion in response["result"]]

    assert set(returned_completion_list) == set(completion_list)

    output.close()
