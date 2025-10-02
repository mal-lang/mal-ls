import typing

import pytest

from malls.lsp.enums import ErrorCodes

from ...util import CONTENT_TYPE_HEADER, build_rpc_message_stream, find_last_request


@pytest.fixture
def client_requests() -> list[dict]:
    """
    Keeps track of all requests from the client made so far.

    Has to be manually requested and added to.
    """
    return []


@pytest.fixture
def client_notifications() -> list[dict]:
    """
    Keeps track of all notifications from the client made so far.

    Has to be manually requested and added to.
    """
    return []


@pytest.fixture
def client_responses() -> list[dict]:
    """
    Keeps track of all responses from the client made so far.

    Has to be manually requested and added to.
    """
    return []


@pytest.fixture
def client_messages() -> list[dict]:
    """
    Keeps track of all messages from the client made so far.

    Has to be manually requested and added to.
    """
    return []


@pytest.fixture
def server_requests() -> list[dict]:
    """
    Keeps track of all requests from the server made so far.

    Has to be manually requested and added to.
    """
    return []


@pytest.fixture
def server_notifications() -> list[dict]:
    """
    Keeps track of all notifications from the server made so far.

    Has to be manually requested and added to.
    """
    return []


@pytest.fixture
def server_responses() -> list[dict]:
    """
    Keeps track of all responses from the server made so far.

    Has to be manually requested and added to.
    """
    return []


@pytest.fixture
def server_messages() -> list[dict]:
    """
    Keeps track of all messages from the server made so far.

    Has to be manually requested and added to. If creatin
    """
    return []


@pytest.fixture
def initalize_request(client_requests: list[dict], client_messages: list[dict]) -> dict:
    """
    Defines an `initalize` LSP request from client to server.
    """
    message = {
        "jsonrpc": "2.0",
        "id": len(client_requests),
        "method": "initialize",
        "params": {
            "capabilities": {
                "textDocument": {
                    "definition": {"dynamicRegistration": False},
                    "synchronization": {"dynamicRegistration": False},
                }
            },
            "trace": "off",
        },
    }
    client_requests.append(message)
    client_messages.append(message)
    return message


@pytest.fixture
def initalize_response(
    client_requests: list[dict], server_responses: list[dict], server_messages: list[dict]
) -> dict:
    """
    Creates a default response to the latest (id) `initalize` request from a client.
    Defaults to ID 0.
    """
    message = {
        "jsonrpc": "2.0",
        "id": find_last_request(client_requests, "initalize", {}).get("id", 0),
        "result": {
            # TODO: Replace with values from an actual server instance (e.g. via instance.capabilities())  # noqa: E501
            "capabilities": {
                "positionEncoding": "utf-16",
                "textDocumentSync": {"openClose": True, "change": 1},
                "definitionProvider": True,
                "completionProvider": {},
                "hoverProvider": True,
            },
            # TODO: Replace with values from an actual server instance (e.g. via instance.server_info())  # noqa: E501
            "serverInfo": {"name": "mal-language-server"},
        },
    }
    server_responses.append(message)
    server_messages.append(message)
    return message


@pytest.fixture
def initalized_notification(client_notifications: list[dict], client_messages: list[dict]) -> dict:
    """
    Defines an `initalized` LSP notification from client to server.
    """
    message = {"jsonrpc": "2.0", "method": "initialized"}
    client_notifications.append(message)
    client_messages.append(message)
    return message


@pytest.fixture
def shutdown_request(client_requests: list[dict], client_messages: list[dict]) -> dict:
    """
    Defines an `shutdown` LSP request from client to server.
    """
    message = {"jsonrpc": "2.0", "id": len(client_requests), "method": "shutdown"}
    client_requests.append(message)
    client_messages.append(message)
    return message


@pytest.fixture
def exit_notification(client_notifications: list[dict], client_messages: list[dict]) -> dict:
    """
    Defines an `exit` LSP notification from client to server.
    """
    message = {"jsonrpc": "2.0", "method": "exit"}
    client_notifications.append(message)
    client_messages.append(message)
    return message


@pytest.fixture
def invalid_request_response(server_responses: list[dict]) -> dict:
    """
    Defines a template "invalid request" response. Field "message" and "id" must be filled in when
    appropriate.
    """
    message = {
        "jsonrpc": "2.0",
        "error": {
            "code": ErrorCodes.InvalidRequest,
            "message": "Must wait for `initalized` notification before other requests.",
        },
    }
    server_responses.append(message)
    return message


@pytest.fixture
def non_initialized_invalid_request_response(
    server_responses: list[dict], invalid_request_response: dict
) -> None:
    """
    Defines a invalid request response for the case of a non-initalized server.
    """
    message = "Must wait for `initalized` notification before other requests."
    server_responses[-1]["error"]["message"] = message


@pytest.fixture
def client_rpc_messages(client_messages: list[dict]) -> typing.BinaryIO:
    """
    Builds the list of client messages into JSON RPC message stream.
    """
    return build_rpc_message_stream(client_messages)


@pytest.fixture
def server_rpc_messages(server_messages: list[dict]) -> typing.BinaryIO:
    """
    Builds the list of server messages into JSON RPC message stream.
    """
    return build_rpc_message_stream(server_messages, insert_header=CONTENT_TYPE_HEADER)


@pytest.fixture
def did_open_notification(client_notifications: list[dict], client_messages: list[dict]) -> dict:
    """
    Defines an `textDocument/didOpen` LSP notification from client to server. Fields
    `uri` and `text` in `params.textDocument` must be edited.
    """
    message = {
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "languageId": "mal",
                "version": 0,
            }
        },
    }
    client_notifications.append(message)
    client_messages.append(message)
    return message


@pytest.fixture
def did_change_notification(client_notifications: list[dict], client_messages: list[dict]) -> dict:
    """
    Defines an `textDocument/didChange` LSP notification from client to server. Fields
    `uri`, `version` in `params.textDocument` and `range`, `text` in `params.contentChanges`
    must be edited.
    """
    message = {
        "jsonrpc": "2.0",
        "method": "textDocument/didChange",
        "params": {
            "textDocument": {},
            "contentChanges": [
                {
                    "range": {
                        "start": {},
                        "end": {},
                    },
                }
            ],
        },
    }
    client_notifications.append(message)
    client_messages.append(message)
    return message


@pytest.fixture
def client_initalize_procedures(initalize_request, initalized_notification):
    """
    Adds the relevant messages from client to server so that both client and server are initalized.
    """
    pass


@pytest.fixture
def client_shutdown_procedures(shutdown_request, exit_notification):
    """
    Adds the relevant messages from client to server to shut down the server. Assumes at
    non-erreneous and post-initalized server state.
    """
    pass
