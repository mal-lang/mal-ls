import tree_sitter_mal as ts_mal
import pytest
from tree_sitter import Language, Parser
from pathlib import Path

from malls.lsp.classes import Document
from malls.lsp.utils import recursive_parsing
from malls.ts.utils import INCLUDED_FILES_QUERY, find_meta_comment_function, run_query

MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)
FILE_PATH = str(Path(__file__).parent.parent.resolve()) + "/fixtures/mal/"

parameters = [
    ((3, 12), [b"dev cat", b"mod cat"]),
    ((8, 22), [b"dev asset", b"mod asset"]),
    ((13, 13), [b"dev attack_step", b"mod attack_step"]),
    ((12, 18), [b"dev asset3", b"mod asset3"]),
    ((16, 12), [b"dev asset3", b"mod asset3"]),
    ((19, 15), [b"dev asset4", b"mod asset4"]),
]

@pytest.mark.parametrize(
    "point,comments",
    [(point, comment) for point, comment in parameters],
)
def test_find_meta_comment_function(mal_find_meta_comment_function, point, comments):
    # build the storage (mimicks the file parsing in the server)
    storage = {}

    doc_uri = FILE_PATH + "find_meta_comment_function.mal"
    source_encoded = mal_find_meta_comment_function.read()
    tree = PARSER.parse(source_encoded)

    storage[doc_uri] = Document(tree, source_encoded, doc_uri)

    # obtain the included files
    root_node = tree.root_node

    captures = run_query(root_node, INCLUDED_FILES_QUERY)
    if "file_name" in captures:
        recursive_parsing(FILE_PATH, captures["file_name"], storage, doc_uri, [])

    ###################################

    # get the node
    cursor = tree.walk()
    while cursor.goto_first_child_for_point(point) is not None:
        continue

    # confirm it's an identifier
    assert cursor.node.type == "identifier"

    # we use sets to ensure order does not matter
    returned_comments = find_meta_comment_function(cursor.node, cursor.node.text, doc_uri, storage)

    assert set(returned_comments) == set(comments)
