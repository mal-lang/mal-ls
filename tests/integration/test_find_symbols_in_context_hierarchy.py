import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser

from malls.ts.utils import find_symbols_in_context_hierarchy

MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)

def test_find_symbols_in_category_hierarchy(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # space between category and asset (category scope)
    point = (4, 0)

    # symbols (identifiers + keywords)
    symbols = [
        ("var",-1),
        ("c",-1),
        ("compromise",-1),
        ("destroy",-1),
        ('Asset1',0),
        ('Asset2',0),
        ('Asset3',0),
    ]
    keywords = [ 
        ("let",-1),
        ("extends",0),
        ("abstract",0),
        ("asset",0),
        ("category",1),
        ("associations",1),
    ]

    # we use sets to ensure order does not matter
    returned_user_symbols, returned_keywords = find_symbols_in_context_hierarchy(tree.walk(), point)

    assert len(returned_user_symbols.keys()) == len(symbols)
    assert len(returned_keywords.keys()) == len(keywords)

    # check hierarchy levels are correct
    for symbol, lvl in symbols:
        assert symbol in returned_user_symbols
        assert returned_user_symbols[symbol][1] == lvl
    for keyword, lvl in keywords:
        assert keyword in returned_keywords
        assert returned_keywords[keyword][1] == lvl

def test_find_symbols_in_associations_hierarchy(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # space between category and asset (category scope)
    point = (17, 0)

    # symbols (identifiers + keywords)
    symbols = [
        ("a",0),
        ("c",0),
        ("d",0),
        ("e",0),
        ("L",0),
        ("M",0),
    ]
    keywords = [ 
        ("info",0),
        ("category",1),
        ("associations",1),
    ]

    # we use sets to ensure order does not matter
    returned_user_symbols, returned_keywords = find_symbols_in_context_hierarchy(tree.walk(), point)

    assert len(returned_user_symbols.keys()) == len(symbols)
    assert len(returned_keywords.keys()) == len(keywords)

    # check hierarchy levels are correct
    for symbol, lvl in symbols:
        assert symbol in returned_user_symbols
        assert returned_user_symbols[symbol][1] == lvl
    for keyword, lvl in keywords:
        assert keyword in returned_keywords
        assert returned_keywords[keyword][1] == lvl

def test_find_symbols_in_asset1_hierarchy(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # space between category and asset (category scope)
    point = (6, 4)

    # symbols (identifiers + keywords)
    symbols = [
        ("var",0),
        ("c",0),
        ("compromise",0),
        ("destroy",0),
        ('Asset1',1),
        ('Asset2',1),
        ('Asset3',1),
    ]
    keywords = [ 
        ("let",0),
        ("extends",1),
        ("abstract",1),
        ("asset",1),
        ("category",2),
        ("associations",2),
    ]

    # we use sets to ensure order does not matter
    returned_user_symbols, returned_keywords = find_symbols_in_context_hierarchy(tree.walk(), point)

    assert len(returned_user_symbols.keys()) == len(symbols)
    assert len(returned_keywords.keys()) == len(keywords)

    # check hierarchy levels are correct
    for symbol, lvl in symbols:
        assert symbol in returned_user_symbols
        assert returned_user_symbols[symbol][1] == lvl
    for keyword, lvl in keywords:
        assert keyword in returned_keywords
        assert returned_keywords[keyword][1] == lvl

def test_find_symbols_in_asset2_hierarchy(mal_find_symbols_in_scope):
    tree = PARSER.parse(mal_find_symbols_in_scope.read())

    # space between category and asset (category scope)
    point = (12, 4)

    # symbols (identifiers + keywords)
    symbols = [
        ("destroy",0),
        ('Asset1',1),
        ('Asset2',1),
        ('Asset3',1),
    ]
    keywords = [ 
        ("extends",1),
        ("abstract",1),
        ("asset",1),
        ("category",2),
        ("associations",2),
    ]

    # we use sets to ensure order does not matter
    returned_user_symbols, returned_keywords = find_symbols_in_context_hierarchy(tree.walk(), point)

    assert len(returned_user_symbols.keys()) == len(symbols)
    assert len(returned_keywords.keys()) == len(keywords)

    # check hierarchy levels are correct
    for symbol, lvl in symbols:
        assert symbol in returned_user_symbols
        assert returned_user_symbols[symbol][1] == lvl
    for keyword, lvl in keywords:
        assert keyword in returned_keywords
        assert returned_keywords[keyword][1] == lvl

