import logging

import pytest

from malls.lsp.fsm import LifecycleState

from ..util import FakeLanguageServer

log = logging.getLogger(__name__)

# mute_ls from integration conftest

def test_ls_lifecycle_start(mute_ls: FakeLanguageServer):
    assert mute_ls.state == LifecycleState.START

@pytest.fixture
def mute_ls_initalize_empty_response(mute_ls: FakeLanguageServer) -> dict:
    return mute_ls.m_initialize()

def test_initalize_response_server_name(mute_ls_initalize_empty_response: dict):
    assert mute_ls_initalize_empty_response.get("serverInfo", {}).get("name") == "malls"

@pytest.mark.xfail(reason="Central version management/version injection not implemented")
def test_initalize_response_server_version(mute_ls_initalize_empty_response: dict):
    assert mute_ls_initalize_empty_response.get("serverInfo", {}).get("version") is not None

@pytest.fixture
def mute_ls_initalize_empty(mute_ls: FakeLanguageServer) -> FakeLanguageServer:
    mute_ls.m_initialize()
    return mute_ls
