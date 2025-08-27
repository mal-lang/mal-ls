import typing

import pytest

pytest_plugins = ["tests.fixtures.lsp.conftest"]


@pytest.fixture
def wrong_trace_initalize_requests(client_requests: list[dict], initalize_request) -> dict:
    client_requests[-1]["params"]["trace"] = "odf"


@pytest.fixture
def wrong_trace_value_client_messages(
    wrong_trace_initalize_requests,
    initalized_notification,
    shutdown_request,
    exit_notification,
    client_rpc_messages: typing.BinaryIO,
) -> typing.BinaryIO:
    return client_rpc_messages


@pytest.fixture
def set_trace_notification(client_notifications: list[dict], client_messages: list[dict]) -> dict:
    """
    Sends a $/setTrace notification from the client to the server.
    `value` must be set in params.
    """
    message = {"jsonrpc": "2.0", "method": "$/setTrace", "params": {}}
    client_notifications.append(message)
    client_messages.append(message)
    return message


@pytest.fixture
def set_trace_verbose_notification(client_notifications: list[dict], set_trace_notification):
    client_notifications[-1]["params"]["value"] = "verbose"


@pytest.fixture
def set_trace_verbose_client_messages(
    client_initalize_procedures,
    set_trace_verbose_notification,
    client_shutdown_procedures,
    client_rpc_messages: typing.BinaryIO,
) -> typing.BinaryIO:
    return client_rpc_messages


@pytest.fixture
def set_trace_messages_notification(client_notifications: list[dict], set_trace_notification):
    client_notifications[-1]["params"]["value"] = "messages"


@pytest.fixture
def set_trace_messages_client_messages(
    client_initalize_procedures,
    set_trace_messages_notification,
    client_shutdown_procedures,
    client_rpc_messages: typing.BinaryIO,
) -> typing.BinaryIO:
    return client_rpc_messages


@pytest.fixture
def set_trace_off_notification(client_notifications: list[dict], set_trace_notification):
    client_notifications[-1]["params"]["value"] = "off"


@pytest.fixture
def set_trace_off_client_messages(
    client_initalize_procedures,
    set_trace_off_notification,
    client_shutdown_procedures,
    client_rpc_messages: typing.BinaryIO,
) -> typing.BinaryIO:
    return client_rpc_messages


@pytest.fixture
def set_trace_wrong_notification(client_notifications: list[dict], set_trace_notification):
    client_notifications[-1]["params"]["value"] = "vxrbxsx"


@pytest.fixture
def set_trace_wrong_client_messages(
    client_initalize_procedures,
    set_trace_wrong_notification,
    client_shutdown_procedures,
    client_rpc_messages: typing.BinaryIO,
) -> typing.BinaryIO:
    return client_rpc_messages
