import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser

from malls.ts.utils import find_symbol_definition

MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)


def test_symbol_definition_in_category_declaration(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # go to name of category
    point = (3, 12)

    # get the node
    cursor = tree.walk()
    while (cursor.goto_first_child_for_point(point) != None): continue

    # confirm it's an identifier
    assert cursor.node.type == 'identifier'

    # we use sets to ensure order does not matter
    response = find_symbol_definition(cursor.node, cursor.node.text)

    # ensure position is start of category declaration
    assert response == (3,0)


def test_symbol_definition_in_asset_declaration(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # go to name of asset
    point = (5, 19)

    # get the node
    cursor = tree.walk()
    while (cursor.goto_first_child_for_point(point) != None): continue

    # confirm it's an identifier
    assert cursor.node.type == 'identifier'

    # we use sets to ensure order does not matter
    response = find_symbol_definition(cursor.node, cursor.node.text)

    # ensure position is start of asset declaration
    # we have to make sure we ignore whitespaces,
    # the only thing that maters are non-empty characters
    assert response == (5,4)
