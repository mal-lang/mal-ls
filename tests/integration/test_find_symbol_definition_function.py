import logging
from pathlib import Path

import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser

from malls.lsp.classes import Document
from malls.lsp.utils import recursive_parsing
from malls.ts.utils import INCLUDED_FILES_QUERY, find_symbol_definition, run_query

log = logging.getLogger(__name__)
MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)
FILE_PATH = str(Path(__file__).parent.parent.resolve()) + "/fixtures/mal/"


def test_symbol_definition_in_category_declaration(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # go to name of category
    point = (3, 12)

    # get the node
    cursor = tree.walk()
    while cursor.goto_first_child_for_point(point) is not None:
        continue

    # confirm it's an identifier
    assert cursor.node.type == "identifier"

    response = find_symbol_definition(cursor.node, cursor.node.text)

    # ensure position is start of category declaration
    assert response == (3, 0)


def test_symbol_definition_in_asset_declaration_asset_name(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # go to name of asset
    point = (11, 10)

    # get the node
    cursor = tree.walk()
    while cursor.goto_first_child_for_point(point) is not None:
        continue

    # confirm it's an identifier
    assert cursor.node.type == "identifier"

    response = find_symbol_definition(cursor.node, cursor.node.text)

    # ensure position is start of asset declaration
    # we have to make sure we ignore whitespaces,
    # the only thing that maters are non-empty characters
    assert response == (11, 4)


def test_symbol_definition_in_asset_declaration_extended_asset(
    mal_symbol_def_extended_asset_main,
):
    # build the storage (mimicks the file parsing in the server)
    storage = {}

    doc_uri = FILE_PATH + "symbol_def_extended_asset_main.mal"
    source_encoded = mal_symbol_def_extended_asset_main.read()
    tree = PARSER.parse(source_encoded)

    storage[doc_uri] = Document(tree, source_encoded, doc_uri)

    # obtain the included files
    root_node = tree.root_node

    captures = run_query(root_node, INCLUDED_FILES_QUERY)
    recursive_parsing(FILE_PATH, captures["file_name"], storage, doc_uri)

    ###################################

    # go to name of asset
    point = (6, 25)

    # get the node
    cursor = tree.walk()
    while cursor.goto_first_child_for_point(point) is not None:
        continue

    # confirm it's an identifier
    assert cursor.node.type == "identifier"

    # we use sets to ensure order does not matter
    response = find_symbol_definition(cursor.node, cursor.node.text, doc_uri, storage)

    # ensure position is start of asset declaration
    # found in the 3rd auxiliary file
    assert response == (2, 4)


def test_symbol_definition_in_asset_variable(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # go to name of variable
    point = (7, 10)

    # get the node
    cursor = tree.walk()
    while cursor.goto_first_child_for_point(point) is not None:
        continue

    # confirm it's an identifier
    assert cursor.node.type == "identifier"

    response = find_symbol_definition(cursor.node, cursor.node.text)

    # ensure position is start of asset declaration
    # we have to make sure we ignore whitespaces,
    # the only thing that maters are non-empty characters
    assert response == (7, 6)


def test_symbol_definition_in_attack_step(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # go to name of variable
    point = (8, 10)

    # get the node
    cursor = tree.walk()
    while cursor.goto_first_child_for_point(point) is not None:
        continue

    # confirm it's an identifier
    assert cursor.node.type == "identifier"

    response = find_symbol_definition(cursor.node, cursor.node.text)

    # ensure position is start of asset declaration
    # we have to make sure we ignore whitespaces,
    # the only thing that maters are non-empty characters
    assert response == (8, 8)
