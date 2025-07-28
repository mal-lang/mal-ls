import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser

from malls.ts.utils import find_symbols_in_current_scope

MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)

def test_find_symbols_in_category_scope(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # space between category and asset (category scope)
    point = (4, 0)

    # symbols (identifiers + keywords)
    symbols = [
        "Asset1",
        "Asset2",
        "extends",
        "abstract",
        "asset",
        "info"
    ]

    # we use sets to ensure order does not matter
    assert set(find_symbols_in_current_scope(tree.walk(), point)) == set(symbols)

def test_find_symbols_in_association_scope(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # position in association scope
    point = (17, 0)

    # symbols (identifiers + keywords)
    symbols = [
        "a",
        "c",
        "d",
        "e",
        "L",
        "M",
        "info",
    ]

    # we use sets to ensure order does not matter
    assert set(find_symbols_in_current_scope(tree.walk(), point)) == set(symbols)

def test_find_symbols_in_asset1_scope(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # position in Asset1 scope
    point = (7, 10)

    # symbols (identifiers + keywords)
    symbols = [
        "var",
        "c",
        "compromise",
        "destroy",
        "let",
        "info",
    ]

    # we use sets to ensure order does not matter
    assert set(find_symbols_in_current_scope(tree.walk(), point)) == set(symbols)

def test_find_symbols_in_asset2_scope(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # position in Asset2 scope
    point = (13, 10)

    # symbols (identifiers + keywords)
    symbols = [
        "destroy",
        "let",
        "info",
    ]

    # we use sets to ensure order does not matter
    assert set(find_symbols_in_current_scope(tree.walk(), point)) == set(symbols)

def test_find_symbols_in_root_node_scope(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # position in Asset2 scope
    point = (1, 0)

    # symbols (identifiers + keywords)
    symbols = [
        "category",
        "associations",
        "info",
    ]

    # we use sets to ensure order does not matter
    assert set(find_symbols_in_current_scope(tree.walk(), point)) == set(symbols)
