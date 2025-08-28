import pytest
from tree_sitter import TreeCursor

from malls.ts.utils import find_symbols_in_context_hierarchy

# (syntax tree/ts point, expected user symbols + level, expected keywords + level)
parameters = [
    (
        (4, 0),
        [
            ("var", -1),
            ("c", -1),
            ("compromise", -1),
            ("destroy", -1),
            ("Asset1", 0),
            ("Asset2", 0),
            ("Asset3", 0),
        ],
        [
            ("let", -1),
            ("extends", 0),
            ("abstract", 0),
            ("asset", 0),
            ("info", 1),
            ("category", 1),
            ("associations", 1),
        ],
    ),
    (
        (17, 0),
        [("a", 0), ("c", 0), ("d", 0), ("e", 0), ("L", 0), ("M", 0), ("Asset1", 0), ("Asset2", 0)],
        [("info", 1), ("category", 1), ("associations", 1)],
    ),
    (
        (6, 4),
        [
            ("var", 0),
            ("c", 0),
            ("compromise", 0),
            ("destroy", 0),
            ("Asset1", 1),
            ("Asset2", 1),
            ("Asset3", 1),
        ],
        [
            ("let", 0),
            ("extends", 1),
            ("abstract", 1),
            ("asset", 1),
            ("category", 2),
            ("associations", 2),
            ("info", 2),
        ],
    ),
    (
        (12, 4),
        [("destroy", 0), ("Asset1", 1), ("Asset2", 1), ("Asset3", 1)],
        [
            ("let", 0),
            ("extends", 1),
            ("abstract", 1),
            ("asset", 1),
            ("category", 2),
            ("associations", 2),
            ("info", 2),
        ],
    ),
    (
        (0, 0),
        [
            ("var", -2),
            ("compromise", -2),
            ("destroy", -2),
            ("Asset1", -1),
            ("Asset2", -1),
            ("Asset3", -1),
            ("a", -1),
            ("d", -1),
            ("e", -1),
            ("L", -1),
            ("M", -1),
            ("c", -1),
        ],
        [
            ("let", -2),
            ("extends", -1),
            ("abstract", -1),
            ("asset", -1),
            ("info", -1),
            ("category", 0),
            ("associations", 0),
        ],
    ),
]

parameter_ids = ["category", "associations", "asset1", "asset2", "root_node"]

pytest_plugins = ["tests.unit.test_find_symbols_in_scope"]


@pytest.mark.parametrize("point,expected_symbols,expected_keywords", parameters, ids=parameter_ids)
def test_find_symbols_in_hierarchy(
    point: (int, int),
    expected_symbols: list[(str, int)],
    expected_keywords: list[(str, int)],
    find_symbols_in_scope_cursor: TreeCursor,
):
    user_symbols, keywords = find_symbols_in_context_hierarchy(find_symbols_in_scope_cursor, point)

    assert len(user_symbols.keys()) == len(expected_symbols)
    assert len(keywords.keys()) == len(expected_keywords)

    # check hierarchy levels are correct
    for symbol, lvl in expected_symbols:
        assert symbol in user_symbols
        assert user_symbols[symbol][1] == lvl
    for keyword, lvl in expected_keywords:
        assert keyword in keywords
        assert keywords[keyword][1] == lvl
