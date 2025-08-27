from io import BytesIO

import pytest

from malls.lsp.fsm import LifecycleState

from ..util import FakeLanguageServer


@pytest.fixture
def mute_ls() -> FakeLanguageServer:
    ls = FakeLanguageServer(BytesIO(), BytesIO())
    yield ls
    if ls.state.current_state != LifecycleState.EXIT:
        ls.m_exit()
