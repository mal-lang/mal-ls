import tree_sitter_mal as ts_mal
import pytest
from tree_sitter import Language, Parser

from malls.ts.utils import find_meta_comment_function

MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)

parameters = [
    ((3, 12), [b"dev cat", b"mod cat"]),
    ((8, 22), [b"dev asset", b"mod asset"]),
]

@pytest.mark.parametrize(
    "point,comments",
    [(point, comment) for point, comment in parameters],
)
def test_find_meta_comment_function(mal_find_meta_comment_function, point, comments):
    tree = PARSER.parse(mal_find_meta_comment_function.read())

    # get the node
    cursor = tree.walk()
    while cursor.goto_first_child_for_point(point) is not None:
        continue

    # confirm it's an identifier
    assert cursor.node.type == "identifier"

    # we use sets to ensure order does not matter
    returned_comments = find_meta_comment_function(cursor.node, cursor.node.text)

    assert set(returned_comments) == set(comments)
