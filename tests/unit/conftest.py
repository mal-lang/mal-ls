from io import BytesIO

import pytest
import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser

from malls.lsp.fsm import LifecycleState

from ..util import FakeLanguageServer


@pytest.fixture
def mute_ls() -> FakeLanguageServer:
    ls = FakeLanguageServer(BytesIO(), BytesIO())
    yield ls
    if ls.state.current_state != LifecycleState.EXIT:
        ls.m_exit()

@pytest.fixture
def mal_language() -> Language:
    return Language(ts_mal.language())

@pytest.fixture
def utf8_mal_parser(mal_language: Language) -> Parser:
    return Parser(mal_language)
