import asyncio
import io
import logging
import typing

from malls.lsp.enums import ErrorCodes
from malls.lsp.fsm import LifecycleState
from malls.mal_lsp import MALLSPServer

from ..util import get_lsp_json

log = logging.getLogger(__name__)

# wait for most 5s (arbitrary)
MAX_TIMEOUT = 2


class SteppedBytesIO(io.BytesIO):
    """
    SteppedBytesIO provide a way to stop the closing of the IO N-1 times, closing on the Nth time.
    """

    def __init__(self, initial_bytes: bytes = b"", steps: int = 1):
        self.steps = steps

    def close(self):
        if self.steps <= 0:
            super(io.BytesIO, self).close()
        else:
            self.steps -= 1


# TODO: create fake endpoint class (or similar) so the input can be stepped


# https://github.com/python-lsp/python-lsp-server/blob/develop/pylsp/python_lsp.py#L58
def server_output(
    input: typing.BinaryIO, timeout: float | None = MAX_TIMEOUT
) -> typing.Tuple[typing.BinaryIO, MALLSPServer, TimeoutError | None]:
    intermediary = SteppedBytesIO()
    ls = MALLSPServer(input, intermediary)
    time_out_err = None

    async def run_server():
        ls.start()

    try:
        server_future = run_server()
        asyncio.run(asyncio.wait_for(server_future, 1))
    except TimeoutError as e:
        ls.m_exit()
        time_out_err = e
    except Exception as e:
        intermediary.close()
        raise e

    return intermediary, ls, time_out_err


def test_correct_base_lifecycle(init_exit_in: typing.BinaryIO, init_exit_out: typing.BinaryIO):
    output, *_ = server_output(init_exit_in)

    assert output.getvalue() == init_exit_out.read().strip()
    output.close()


def test_pre_initialized_exit_does_not_change_state(pre_initialized_exit_in: typing.BinaryIO):
    output, ls, *_ = server_output(pre_initialized_exit_in)

    assert ls.state.current_state == LifecycleState.INITIALIZE
    output.close()


def test_pre_initialized_shutdown_does_not_change_state(
    pre_initialized_shutdown_in: typing.BinaryIO,
):
    output, ls, *_ = server_output(pre_initialized_shutdown_in)

    assert ls.state.current_state == LifecycleState.INITIALIZE
    output.close()


def test_pre_initialized_shutdown_errs(pre_initialized_shutdown_in: typing.BinaryIO):
    output, ls, *_ = server_output(pre_initialized_shutdown_in)

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
