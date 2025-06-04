import asyncio
import io
import logging
import typing

from malls.mal_lsp import MALLSPServer
from malls.lsp.fsm import LifecycleState

log = logging.getLogger(__name__)

# wait for most 5s (arbitrary)
MAX_TIMEOUT=5

class SteppedBytesIO(io.BytesIO):
    """
    SteppedBytesIO provide a way to stop the closing of the IO N-1 times, closing on the Nth time.
    """
    def __init__(self, initial_bytes: bytes = b'', steps: int = 1):
        self.steps = steps

    def close(self):
        if self.steps <= 0:
            super(io.BytesIO, self).close()
        else:
            self.steps -= 1

async def server_output(
        input: typing.BinaryIO,
        timeout: float | None = MAX_TIMEOUT) -> typing.Tuple[typing.BinaryIO, MALLSPServer]:
    intermediary = SteppedBytesIO()
    ls = MALLSPServer(input, intermediary)

    async def run_server():
        ls.start()
    try:
        await asyncio.wait_for(run_server(), timeout=timeout)
    except Exception as e:
        intermediary.close()
        raise e

    return intermediary, ls


async def test_correct_base_lifecycle(
        init_exit_in: typing.BinaryIO,
        init_exit_out: typing.BinaryIO):
    output, _ = await server_output(init_exit_in)

    assert output.getvalue() == init_exit_out.read()
    output.close()

async def test_pre_initialized_exit_does_not_change_state(
        pre_initialized_exit_in: typing.BinaryIO):
    output, ls = await server_output(pre_initialized_exit_in)

    assert ls.state.current_state == LifecycleState.INITIALIZE
    output.close()
