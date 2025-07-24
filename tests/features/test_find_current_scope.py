import typing
from malls.lsp.enums import PositionEncodingKind
from malls.mal_lsp import MALLSPServer
import io
from tree_sitter import Language, Parser, QueryCursor
import tree_sitter_mal as ts_mal

FILE = open("./tests/mal_fixtures/test_find_current_scope.mal","rb")
SOURCE = FILE.read()
MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)
TREE = PARSER.parse(SOURCE)

class FakeLanguageServer(MALLSPServer):
    def __init__(self):
        super().__init__(io.BytesIO, io.BytesIO)

    def find_current_scope(self, cursor, point):
        return self._find_current_scope(cursor, point)

def test_find_current_scope_1():
    fakeLSP = FakeLanguageServer()

    # space between category and asset
    point = (4,0)
    assert fakeLSP.find_current_scope(TREE.walk(), point).type == "category_declaration"

def test_find_current_scope_2():
    fakeLSP = FakeLanguageServer()

    # inside the asset declaration
    point = (7,13)
    assert fakeLSP.find_current_scope(TREE.walk(), point).type == "asset_declaration"

def test_find_current_scope_3():
    fakeLSP = FakeLanguageServer()

    # inside the association declaration
    point = (17,19)
    assert fakeLSP.find_current_scope(TREE.walk(), point).type == "associations_declaration"

def test_find_current_scope_4():
    fakeLSP = FakeLanguageServer()

    # outside all components
    point = (1,10)
    assert fakeLSP.find_current_scope(TREE.walk(), point).type == 'source_file'

def test_find_current_scope_5():
    fakeLSP = FakeLanguageServer()

    # on the name of the asset
    point = (10,10)
    assert fakeLSP.find_current_scope(TREE.walk(), point).type == "category_declaration"

def test_find_current_scope_6():
    fakeLSP = FakeLanguageServer()

    # on the '{' of the asset
    point = (11,4)
    assert fakeLSP.find_current_scope(TREE.walk(), point).type == "asset_declaration"

def test_find_current_scope_7():
    fakeLSP = FakeLanguageServer()

    # on the '}' of the asset
    point = (13,4)
    assert fakeLSP.find_current_scope(TREE.walk(), point).type == "asset_declaration"

def test_find_current_scope_8():
    fakeLSP = FakeLanguageServer()

    # on the name of the category
    point = (3,10)
    assert fakeLSP.find_current_scope(TREE.walk(), point).type == 'source_file'

def test_find_current_scope_9():
    fakeLSP = FakeLanguageServer()

    # on the '{' of the category 
    point = (3,17)
    assert fakeLSP.find_current_scope(TREE.walk(), point).type == "category_declaration"

def test_find_current_scope_10():
    fakeLSP = FakeLanguageServer()

    # on the term 'associations'
    point = (15,4)
    assert fakeLSP.find_current_scope(TREE.walk(), point).type == 'source_file'

def test_find_current_scope_11():
    fakeLSP = FakeLanguageServer()

    # on the '{' of the association
    point = (18,0)
    assert fakeLSP.find_current_scope(TREE.walk(), point).type == "associations_declaration"
