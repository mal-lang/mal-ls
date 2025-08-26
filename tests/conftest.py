import logging
import os
import sys
import typing
from io import BytesIO
from pathlib import Path

# from ..src.malls.lsp.enums import ErrorCodes
import pytest
import uritools

from malls.lsp.enums import ErrorCodes

from .util import (
    CONTENT_TYPE_HEADER,
    build_rpc_message_stream,
    find_last_request,
)

logging.getLogger().setLevel(logging.DEBUG)
log = logging.getLogger(__name__)

module = sys.modules[__name__]
# Generate pytest fixtures from all fixture files in 'fixtures' and its subdirectories
for directory, _, files in os.walk("tests/fixtures"):
    if "__pycache__" in directory:
        continue
    for file_name in files:
        if file_name.endswith(".py") or file_name == "__pycache__":
            continue
        # Remove extension, e.g: .http/.lsp/.mal
        fixture_name = file_name[: file_name.rindex(".")]
        # Replace dots with underscore, e.g: empty.out -> empty_out
        fixture_name = fixture_name.replace(".", "_")
        # Add subdirectory path as prefix if there was one
        if len(directory) > len("tests/fixtures"):
            post_test_dir_index = directory.find("fixtures")
            # Remove up until tests plus directory delimiter
            fixture_prefix = directory[post_test_dir_index + len("fixtures") + 1 :]
            # Replace directory delimiters with underscores
            fixture_prefix = fixture_prefix.replace("/", "_").replace("\\", "_")
            fixture_name = fixture_prefix + "_" + fixture_name

        # Get full path of file so its usable by `open`
        file_path = os.path.join(directory, file_name)

        def open_fixture_file(file: str):
            def template() -> typing.BinaryIO:
                with open(file, "rb") as file_descriptor:
                    yield file_descriptor

            file_name = Path(file).name
            template.__doc__ = f"Opens {file_name} in (r)ead (b)inary mode and returns the reader."

            return template

        fixture = pytest.fixture(
            open_fixture_file(file_path),
            name=fixture_name,
        )
        # Bind `fixture` as `fixture_name` inside this module so it gets exported
        setattr(module, fixture_name, fixture)

        def fixture_uri(file: str):
            path = Path(file)
            file_path = path.resolve()
            uri = file_path.as_uri()
            def template() -> str:
                return uri

            file_name = path.name
            template.__doc__ = f"Returns the URI for {file_name} using file scheme."

            return template

        uri_fixture = pytest.fixture(
            fixture_uri(file_path),
            name=fixture_name + "_uri",
        )

        setattr(module, fixture_name + "_uri", uri_fixture)


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
        "params": {"trace": "off", "capabilities": {}},
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
        "id": find_last_request(
            client_requests, lambda request: request.get("method") == "initalize", {}
        ).get("id", 0),
        "result": {
            # TODO: Replace with values from an actual server instance (e.g. via instance.capabilities())
            "capabilities": {
                "positionEncoding": "utf-16",
                "textDocumentSync": {"openClose": True, "change": 1},
                "definitionProvider": True,
                "completionProvider": {},
            },
            # TODO: Replace with values from an actual server instance (e.g. via instance.server_info())
            "serverInfo": {"name": "mal-ls"},
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
def client_rpc_messages(client_messages: list[dict]) -> BytesIO:
    """
    Builds the list of client messages into JSON RPC message stream.
    """
    return build_rpc_message_stream(client_messages)


@pytest.fixture
def server_rpc_messages(server_messages: list[dict]) -> BytesIO:
    """
    Builds the list of server messages into JSON RPC message stream.
    """
    return build_rpc_message_stream(server_messages, insert_header=CONTENT_TYPE_HEADER)
