import asyncio
import io
import typing

from malls.mal_lsp import MALLSPServer

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

async def test_correct_base_lifecycle(init_exit_in: typing.BinaryIO, init_exit_out: typing.BinaryIO):
    intermediary = SteppedBytesIO()
    ls = MALLSPServer(init_exit_in, intermediary)
    async def run_server():
        ls.start()
    try:
        await asyncio.wait_for(run_server(), timeout=MAX_TIMEOUT)
    except Exception as e:
        intermediary.close()
        raise e
    assert intermediary.readlines() == init_exit_out.readlines()
    intermediary.close()

