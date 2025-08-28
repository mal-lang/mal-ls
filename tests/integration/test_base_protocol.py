import typing

from malls.lsp.enums import ErrorCodes
from malls.lsp.fsm import LifecycleState

from ..util import get_lsp_json, server_output

pytest_plugins = ["tests.fixtures.lsp.base_protocol"]


def test_correct_base_lifecycle(
    init_exit_client_messages: typing.BinaryIO, init_exit_server_messages: typing.BinaryIO
):
    output, *_ = server_output(init_exit_client_messages)

    assert output.getvalue() == init_exit_server_messages.read()
    output.close()


def test_pre_initialized_exit_does_not_change_state(init_exit_client_messages: typing.BinaryIO):
    output, ls, *_ = server_output(init_exit_client_messages)

    assert ls.state.current_state == LifecycleState.INITIALIZE
    output.close()


def test_pre_initialized_shutdown_does_not_change_state(
    init_shutdown_client_messages: typing.BinaryIO,
):
    output, ls, *_ = server_output(init_shutdown_client_messages)

    assert ls.state.current_state == LifecycleState.INITIALIZE
    output.close()


def test_pre_initialized_shutdown_errs(init_shutdown_client_messages: typing.BinaryIO):
    output, ls, *_ = server_output(init_shutdown_client_messages)

    # the test and server share the same buffer,
    # so we must reset the cursor
    output.seek(0)

    response = get_lsp_json(output)
    assert "result" in response
    assert "capabilities" in response["result"]

    response = get_lsp_json(output)
    assert "error" in response
    assert "code" in response["error"]
    assert response["error"]["code"] == ErrorCodes.InvalidRequest

    output.close()
