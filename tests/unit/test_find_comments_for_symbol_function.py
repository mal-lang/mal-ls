from pathlib import Path

import pytest
import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser

from malls.lsp.classes import Document
from malls.lsp.utils import recursive_parsing
from malls.ts.utils import INCLUDED_FILES_QUERY, find_comments_function, run_query

MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)
FILE_PATH = str(Path(__file__).parent.parent.resolve()) + "/fixtures/mal/"

parameters = [
    ((9, 13), [b"// category comment"]),
    ((15, 12), [b"// asset comment 1", b"// asset comment 2"]),
    ((29, 12), [b"/* \n     * MULTI-LINE COMMENT\n     */", b"// followed by single comment"]),
    ((33, 12), [b"// attack_step comment"]),
    ((43, 8), []),
    ((47, 6), [b"// asset4 comment"]),
    ((55, 21), [b"// association comment"]),
]


@pytest.mark.parametrize(
    "point,comments",
    parameters,
)
def test_find_comments_for_symbol_function(mal_find_comments_for_symbol_function, point, comments):
    # build the storage (mimicks the file parsing in the server)
    storage = {}

    doc_uri = FILE_PATH + "find_comments_for_symbol_function.mal"
    source_encoded = mal_find_comments_for_symbol_function.read()
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
    returned_comments = [
        x.text for x in find_comments_function(cursor.node, cursor.node.text, doc_uri, storage)
    ]

    assert set(returned_comments) == set(comments)
