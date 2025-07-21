import logging

import pytest

from malls.lsp.enums import ErrorCodes
from malls.lsp.fsm import LifecycleState

from ..util import FakeLanguageServer

log = logging.getLogger(__name__)

# mute_ls from integration conftest


def test_ls_lifecycle_start(mute_ls: FakeLanguageServer):
    assert mute_ls.state.state == LifecycleState.START


failing_methods = ["m_initialized", "m_shutdown", "m_exit", "m_invalid_request_at_start"]
@pytest.mark.parametrize("method", failing_methods)
def test_ls_non_initialize(mute_ls: FakeLanguageServer, method: str):
    method_fn = getattr(mute_ls, method)
    assert method_fn is not None
    response = method_fn()
    assert response.get("error", {}).get("code") == ErrorCodes.InvalidRequest


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
