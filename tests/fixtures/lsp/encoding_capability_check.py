import io

import pytest

# So that importers are aware of the conftest fixtures
pytest_plugins = ["tests.fixtures.lsp.conftest"]


@pytest.fixture
def set_trace_notification(client_notifications: list[dict], client_messages: list[dict]) -> dict:
    message = {"jsonrpc": "2.0", "method": "$/setTrace", "params": {"value": "messages"}}
    client_notifications.append(message)
    client_messages.append(message)
    return message


@pytest.fixture
def encoding_capability_client_messages(
    initalize_request,
    initalized_notification,
    set_trace_notification,
    shutdown_request,
    exit_notification,
    client_rpc_messages: io.BytesIO,
) -> io.BytesIO:
    """
    client              server
    --------------------------
    initialize
    initalized
    $/setTrace
    shutdown
    exit
    """
    return client_rpc_messages
