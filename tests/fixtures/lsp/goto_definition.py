import typing

import pytest

from ...util import build_rpc_message_stream

# So that importers are aware of the conftest fixtures
pytest_plugins = ["tests.fixtures.lsp.conftest"]


type FixtureCallback[T] = typing.Callable[[str, typing.BinaryIO, (int, int)], T]


@pytest.fixture
def open_document_notification(
    client_notifications: list[dict], client_messages: list[dict]
) -> FixtureCallback[dict]:
    def make(uri: str, file: typing.BinaryIO, _location) -> dict:
        message = {
            "jsonrpc": "2.0",
            "method": "textDocument/didOpen",
            "params": {
                "textDocument": {
                    "uri": uri,
                    "languageId": "mal",
                    "version": 0,
                    "text": file.read().decode("utf8"),
                }
            },
        }
        client_notifications.append(message)
        client_messages.append(message)
        return message

    return make


@pytest.fixture
def definition_request(
    client_requests: list[dict], client_messages: list[dict]
) -> FixtureCallback[dict]:
    def make(uri: str, _file, location: (int, int)) -> dict:
        line, char = location
        message = {
            "id": len(client_requests),
            "jsonrpc": "2.0",
            "method": "textDocument/definition",
            "params": {
                "textDocument": {
                    "uri": uri,
                },
                "position": {
                    "line": line,
                    "character": char,
                },
            },
        }
        client_requests.append(message)
        client_messages.append(message)
        return message

    return make


@pytest.fixture
def goto_definition_client_messages(
    client_messages: list[dict],
    initalize_request,
    initalized_notification,
    open_document_notification: FixtureCallback[dict],
    definition_request: FixtureCallback[dict],
) -> FixtureCallback[typing.BinaryIO]:
    def make(uri: str, file: typing.BinaryIO, location: (int, int)) -> typing.BinaryIO:
        args = (uri, file, location)
        open_document_notification(*args)
        definition_request(*args)
        return build_rpc_message_stream(client_messages)

    return make
