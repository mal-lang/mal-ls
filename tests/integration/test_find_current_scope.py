import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser

from malls.ts.utils import find_current_scope

MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)


def test_find_current_scope_on_space_between_category_and_asset(mal_find_current_scope_function):
    tree = PARSER.parse(mal_find_current_scope_function.read())

    # space between category and asset
    point = (4, 0)
    assert find_current_scope(tree.walk(), point).type == "category_declaration"


def test_find_current_scope_inside_the_asset_declaration(mal_find_current_scope_function):
    tree = PARSER.parse(mal_find_current_scope_function.read())

    # inside the asset declaration
    point = (7, 13)
    assert find_current_scope(tree.walk(), point).type == "asset_declaration"


def test_find_current_scope_inside_the_association_declaration(mal_find_current_scope_function):
    tree = PARSER.parse(mal_find_current_scope_function.read())

    # inside the association declaration
    point = (17, 19)
    assert find_current_scope(tree.walk(), point).type == "associations_declaration"


def test_find_current_scope_outside_all_components(mal_find_current_scope_function):
    tree = PARSER.parse(mal_find_current_scope_function.read())

    # outside all components
    point = (1, 10)
    assert find_current_scope(tree.walk(), point).type == "source_file"


def test_find_current_scope_on_name_of_asset(mal_find_current_scope_function):
    tree = PARSER.parse(mal_find_current_scope_function.read())

    # on the name of the asset
    point = (10, 10)
    assert find_current_scope(tree.walk(), point).type == "category_declaration"


def test_find_current_scope_on_bracket_of_asset(mal_find_current_scope_function):
    tree = PARSER.parse(mal_find_current_scope_function.read())

    # on the '{' of the asset
    point = (11, 4)
    assert find_current_scope(tree.walk(), point).type == "asset_declaration"


def test_find_current_scope_on_closing_bracket_of_asset(mal_find_current_scope_function):
    tree = PARSER.parse(mal_find_current_scope_function.read())

    # on the '}' of the asset
    point = (13, 4)
    assert find_current_scope(tree.walk(), point).type == "asset_declaration"


def test_find_current_scope_on_name_of_category(mal_find_current_scope_function):
    tree = PARSER.parse(mal_find_current_scope_function.read())

    # on the name of the category
    point = (3, 10)
    assert find_current_scope(tree.walk(), point).type == "source_file"


def test_find_current_scope_on_bracket_of_category(mal_find_current_scope_function):
    tree = PARSER.parse(mal_find_current_scope_function.read())

    # on the '{' of the category
    point = (3, 17)
    assert find_current_scope(tree.walk(), point).type == "category_declaration"


def test_find_current_scope_on_term_association(mal_find_current_scope_function):
    tree = PARSER.parse(mal_find_current_scope_function.read())

    # on the term 'associations'
    point = (15, 4)
    assert find_current_scope(tree.walk(), point).type == "source_file"


def test_find_current_scope_on_bracket_of_association(mal_find_current_scope_function):
    tree = PARSER.parse(mal_find_current_scope_function.read())

    # on the '{' of the association
    point = (18, 0)
    assert find_current_scope(tree.walk(), point).type == "associations_declaration"
