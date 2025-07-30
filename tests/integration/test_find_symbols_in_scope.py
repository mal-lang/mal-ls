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
    user_symbols = [
        "Asset1",
        "Asset2",
        'Asset3',
    ]
    keywords = [
        "extends",
        "abstract",
        "asset",
    ]

    # we use sets to ensure order does not matter
    returned_user_symbols, returned_keywords = find_symbols_in_current_scope(tree.walk(), point)

    assert set(returned_user_symbols) == set(user_symbols)
    assert set(returned_keywords) == set(keywords)

def test_find_symbols_in_association_scope(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # position in association scope
    point = (17, 0)

    # symbols (identifiers + keywords)
    user_symbols = [
        "a",
        "c",
        "d",
        "e",
        "L",
        "M",
    ]
    keywords = [
        "info",
    ]

    # we use sets to ensure order does not matter
    returned_user_symbols, returned_keywords = find_symbols_in_current_scope(tree.walk(), point)

    assert set(returned_user_symbols) == set(user_symbols)
    assert set(returned_keywords) == set(keywords)

def test_find_symbols_in_asset1_scope(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # position in Asset1 scope
    point = (7, 10)

    # symbols (identifiers + keywords)
    user_symbols = [
        "var",
        "c",
        "compromise",
        "destroy",
    ]
    keywords = [
        "let",
    ]

    # we use sets to ensure order does not matter
    returned_user_symbols, returned_keywords = find_symbols_in_current_scope(tree.walk(), point)

    assert set(returned_user_symbols) == set(user_symbols)
    assert set(returned_keywords) == set(keywords)

def test_find_symbols_in_asset2_scope(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # position in Asset2 scope
    point = (13, 10)

    # symbols (identifiers + keywords)
    user_symbols = [
        "destroy",
    ]
    keywords = [
    ]

    # we use sets to ensure order does not matter
    returned_user_symbols, returned_keywords = find_symbols_in_current_scope(tree.walk(), point)

    assert set(returned_user_symbols) == set(user_symbols)
    assert set(returned_keywords) == set(keywords)

def test_find_symbols_in_root_node_scope(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # position in Asset2 scope
    point = (1, 0)

    # symbols (identifiers + keywords)
    user_symbols = []
    keywords = [
        "category",
        "associations",
        "info",
    ]

    # we use sets to ensure order does not matter
    returned_user_symbols, returned_keywords = find_symbols_in_current_scope(tree.walk(), point)

    assert set(returned_user_symbols) == set(user_symbols)
    assert set(returned_keywords) == set(keywords)
