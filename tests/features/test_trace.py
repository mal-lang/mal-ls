import asyncio
import io
import logging
import typing

from malls.lsp.enums import ErrorCodes, TraceValue
from malls.lsp.fsm import LifecycleState
from malls.mal_lsp import MALLSPServer

from ..util import get_lsp_json, SteppedBytesIO, server_output

log = logging.getLogger(__name__)


def test_wrong_trace_value_in_initialization(
        wrong_trace_value_in: typing.BinaryIO):
    output, ls, *_ = server_output(wrong_trace_value_in)

    # the test and server share the same buffer,
    # so we must reset the cursor
    output.seek(0)

    response = get_lsp_json(output)

    # Ensure there is an error on the response corresponding to invalid
    # parameter, since "traceValue" is wrong
    assert "error" in response
    assert 'code' in response['error']
    assert response['error']['code'] == ErrorCodes.InvalidParams

    output.close()

def test_set_trace_correctly(
        set_trace_value_in: typing.BinaryIO):
    output, ls, *_ = server_output(set_trace_value_in)

    # ensure ls has trace value correctly set
    assert ls.traceValue == TraceValue.Verbose

    output.close()

def test_set_trace_incorrectly(
        set_wrong_trace_value_in: typing.BinaryIO):
    output, ls, *_ = server_output(set_wrong_trace_value_in)

    # ensure ls has trace value correctly set
    assert ls.traceValue == TraceValue.Off

    output.close()

def test_log_trace_messages(
        log_trace_messages_in: typing.BinaryIO):
    output, ls, *_ = server_output(log_trace_messages_in)

    # the test and server share the same buffer,
    # so we must reset the cursor
    output.seek(0)

    # Skip to last message 
    response = get_lsp_json(output)
    response = get_lsp_json(output)
    response = get_lsp_json(output)

    assert "method" in response
    assert "exit" == response['method']
    assert "params" in response
    assert 'message' in response['params']
    assert 'verbose' not in response['params']

    output.close()

def test_log_trace_verbose(
        log_trace_verbose_in: typing.BinaryIO):
    output, ls, *_ = server_output(log_trace_verbose_in)

    # the test and server share the same buffer,
    # so we must reset the cursor
    output.seek(0)

    # Skip to last message 
    response = get_lsp_json(output)
    response = get_lsp_json(output)
    response = get_lsp_json(output)

    assert "method" in response
    assert "exit" == response['method']
    assert "params" in response
    assert 'message' in response['params']
    assert 'verbose' in response['params']

    output.close()

def test_log_trace_off(
        log_trace_off_in: typing.BinaryIO):
    output, ls, *_ = server_output(log_trace_off_in)

    # the test and server share the same buffer,
    # so we must reset the cursor
    output.seek(0)

    # Ensure no notification about exit was sent
    assert b'exit' not in output.getvalue()

    output.close()




