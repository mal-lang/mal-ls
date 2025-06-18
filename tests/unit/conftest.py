import pytest
from io import BytesIO

from ..util import FakeLanguageServer
from malls.lsp.fsm import LifecycleState

@pytest.fixture
def mute_ls() -> FakeLanguageServer:
    ls = FakeLanguageServer(BytesIO(), BytesIO())
    yield ls
    if ls.state.current_state != LifecycleState.EXIT:
        ls.m_exit()
