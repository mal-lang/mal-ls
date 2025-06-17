import logging

from malls.lsp.fsm import LifecycleState

from ..util import FakeLanguageServer

log = logging.getLogger(__name__)

# mute_ls from integration conftest

def test_ls_lifecycle_start(mute_ls: FakeLanguageServer):
    assert mute_ls.state == LifecycleState.START
