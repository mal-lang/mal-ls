import typing

from malls.lsp.enums import ErrorCodes, TraceValue

from ..util import get_lsp_json, server_output

pytest_plugins = ["tests.fixtures.lsp.trace"]


def test_wrong_trace_value_in_initialization(wrong_trace_value_client_messages: typing.BinaryIO):
    output, ls, *_ = server_output(wrong_trace_value_client_messages)

    # the test and server share the same buffer,
    # so we must reset the cursor
    output.seek(0)

    response = get_lsp_json(output)

    # Ensure there is an error on the response corresponding to invalid
    # parameter, since "traceValue" is wrong
    assert "error" in response
    assert "code" in response["error"]
    assert response["error"]["code"] == ErrorCodes.InvalidParams

    output.close()


def test_set_trace_correctly(set_trace_verbose_client_messages: typing.BinaryIO):
    output, ls, *_ = server_output(set_trace_verbose_client_messages)

    # ensure ls has trace value correctly set
    assert ls.trace_value == TraceValue.Verbose

    output.close()


def test_set_trace_incorrectly(set_trace_wrong_client_messages: typing.BinaryIO):
    output, ls, *_ = server_output(set_trace_wrong_client_messages)

    # ensure ls has trace value correctly set
    assert ls.trace_value == TraceValue.Off

    output.close()


def test_log_trace_messages(set_trace_messages_client_messages: typing.BinaryIO):
    output, ls, *_ = server_output(set_trace_messages_client_messages)

    # the test and server share the same buffer,
    # so we must reset the cursor
    output.seek(0)

    # Skip to last message
    response = get_lsp_json(output)
    response = get_lsp_json(output)
    response = get_lsp_json(output)

    assert "method" in response
    assert "exit" == response["method"]
    assert "params" in response
    assert "message" in response["params"]
    assert "verbose" not in response["params"]

    output.close()


def test_log_trace_verbose(set_trace_verbose_client_messages: typing.BinaryIO):
    output, ls, *_ = server_output(set_trace_verbose_client_messages)

    # the test and server share the same buffer,
    # so we must reset the cursor
    output.seek(0)

    # Skip to last message
    response = get_lsp_json(output)
    response = get_lsp_json(output)
    response = get_lsp_json(output)

    assert "method" in response
    assert "exit" == response["method"]
    assert "params" in response
    assert "message" in response["params"]
    assert "verbose" in response["params"]

    output.close()


def test_log_trace_off(set_trace_off_client_messages: typing.BinaryIO):
    output, ls, *_ = server_output(set_trace_off_client_messages)

    # the test and server share the same buffer,
    # so we must reset the cursor
    output.seek(0)

    # Ensure no notification about exit was sent
    assert b"exit" not in output.getvalue()

    output.close()
