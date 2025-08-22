import logging
import os
import sys
import typing
from io import BytesIO

# from ..src.malls.lsp.enums import ErrorCodes
import pytest

from malls.lsp.enums import ErrorCodes

from .util import (
    BASE_OPEN_FILE,
    CHANGE_FILE_1,
    CHANGE_FILE_2,
    CHANGE_FILE_3,
    CHANGE_FILE_4,
    CHANGE_FILE_5,
    CHANGE_FILE_WITH_ERROR,
    COMPLETION_PAYLOADS,
    CONTENT_TYPE_HEADER,
    GOTO_DEFINITION_PAYLOADS,
    OPEN_FILE_WITH_ERROR,
    OPEN_FILE_WITH_FAKE_INCLUDE,
    OPEN_FILE_WITH_INCLUDE_WITH_ERROR,
    OPEN_FILE_WITH_INCLUDED_FILE,
    OPEN_INCLUDED_FILE_WITH_ERROR,
    build_payload,
    build_rpc_message_stream,
    find_last_request,
)

logging.getLogger().setLevel(logging.DEBUG)
log = logging.getLogger(__name__)

module = sys.modules[__name__]
# Generate pytest fixtures from all fixture files in 'fixtures' and its subdirectories
for directory, _, files in os.walk("tests/fixtures"):
    for file_name in files:
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

        def open_fixture_for_writing(file: str, payload: bytes):
            def template() -> typing.BinaryIO:
                with open(file, "rb") as file_descriptor:
                    bio = BytesIO(file_descriptor.read())

                bio.seek(0, 2)
                bio.write(payload)
                bio.seek(0)
                return bio

            return template

        def open_fixture_file(file: str):
            def template() -> typing.BinaryIO:
                """Opens a fixture in (r)ead (b)inary mode. See `open` for more details."""

                with open(file, "rb") as file_descriptor:
                    yield file_descriptor

            return template

        open_fixture_file.__doc__ = open.__doc__

        # Define the fixture from `open_file` on `file_path` as `fixture_name`
        if directory == "tests/fixtures/writeable_fixtures":
            # create different fixtures from the sabe base file
            payloads = (
                [
                    ([BASE_OPEN_FILE], fixture_name + "_base_open_file"),
                    ([OPEN_FILE_WITH_INCLUDED_FILE], fixture_name + "_with_included_file"),
                    ([OPEN_FILE_WITH_FAKE_INCLUDE], fixture_name + "_with_fake_include"),
                    ([BASE_OPEN_FILE, CHANGE_FILE_1], "change_middle_of_file_single_line"),
                    ([BASE_OPEN_FILE, CHANGE_FILE_2], "change_middle_of_file_multiple_lines"),
                    ([BASE_OPEN_FILE, CHANGE_FILE_3], "change_end_of_file"),
                    ([BASE_OPEN_FILE, CHANGE_FILE_4], "change_middle_of_file_twice"),
                    ([BASE_OPEN_FILE, CHANGE_FILE_5], "change_whole_file"),
                    ([OPEN_FILE_WITH_ERROR], "open_file_with_error"),
                    ([OPEN_FILE_WITH_INCLUDE_WITH_ERROR], "open_file_with_include_error"),
                    ([BASE_OPEN_FILE, CHANGE_FILE_WITH_ERROR], "change_file_with_error"),
                    (
                        [OPEN_FILE_WITH_INCLUDE_WITH_ERROR, OPEN_INCLUDED_FILE_WITH_ERROR],
                        "open_file_with_include_error_and_open_file",
                    ),
                ]
                + GOTO_DEFINITION_PAYLOADS
                + COMPLETION_PAYLOADS
            )
            for payload, new_name in payloads:
                fixture = pytest.fixture(
                    open_fixture_for_writing(file_path, build_payload(payload)),
                    name=new_name,
                )
                # Bind `fixture` as `fixture_name` inside this module so it gets exported
                setattr(module, new_name, fixture)
        else:
            fixture = pytest.fixture(
                open_fixture_file(file_path),
                name=fixture_name,
            )
            # Bind `fixture` as `fixture_name` inside this module so it gets exported
            setattr(module, fixture_name, fixture)


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
