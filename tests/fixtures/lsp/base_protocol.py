from io import BytesIO

import pytest


@pytest.fixture
def init_exit_expected_exchange(
    initalize_request,
    initalize_response,
    exit_notification,
    non_initialized_invalid_request_response,
) -> None:
    """
    client              server
    --------------------------
    initialize
                        initalize_response
    exit
                        invalid request
    """
    pass


@pytest.fixture
def init_exit_client_messages(init_exit_expected_exchange, client_rpc_messages: BytesIO) -> BytesIO:
    """
    client              server
    --------------------------
    initialize
                        (initalize_response)
    exit
                        (invalid request)
    """
    return client_rpc_messages


@pytest.fixture
def init_exit_server_messages(init_exit_expected_exchange, server_rpc_messages: BytesIO) -> BytesIO:
    """
    client              server
    -----------------------------------
    (initialize)
                        initalize_response
    (exit)
                        invalid request
    """
    return server_rpc_messages


@pytest.fixture
def init_shutdown_expected_exchange(
    initalize_request,
    initalize_response,
    shutdown_request,
    non_initialized_invalid_request_response,
) -> None:
    """
    client              server
    --------------------------
    initialize
                        initalize_response
    shutdown
                        invalid request
    """
    pass


@pytest.fixture
def init_shutdown_client_messages(
    init_shutdown_expected_exchange, client_rpc_messages: BytesIO
) -> BytesIO:
    """
    client              server
    --------------------------
    initialize
                        (initalize_response)
    shutdown
                        (invalid request)
    """
    return client_rpc_messages


@pytest.fixture
def init_shutdown_server_messages(
    init_shutdown_expected_exchange, server_rpc_messages: BytesIO
) -> BytesIO:
    """
    client              server
    -----------------------------------
    (initialize)
                        initalize_response
    (shutdown)
                        invalid request
    """
    return server_rpc_messages
