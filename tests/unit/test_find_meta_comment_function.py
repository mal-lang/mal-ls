import typing

import pytest
from tree_sitter import Parser, Tree

from malls.lsp.classes import Document
from malls.lsp.utils import recursive_parsing
from malls.ts.utils import INCLUDED_FILES_QUERY, find_meta_comment_function, run_query

parameters = [
    ((3, 12), {b"dev cat", b"mod cat"}),
    ((8, 22), {b"dev asset", b"mod asset"}),
    ((13, 13), {b"dev attack_step", b"mod attack_step"}),
    ((12, 18), {b"dev asset3", b"mod asset3"}),
    ((16, 12), {b"dev asset3", b"mod asset3"}),
    ((19, 15), {b"dev asset4", b"mod asset4"}),
    ((20, 20), {b"dev asset5", b"mod asset5"}),
    ((20, 28), {b"dev attack_step_5", b"mod attack_step_5"}),
    ((54, 12), {b"some info"}),
    ((54, 21), {b"some info"}),
    ((57, 37), {b"dev asset4", b"mod asset4"}),
]


@pytest.fixture
def find_meta_comment_data(mal_find_meta_comment_function: typing.BinaryIO) -> bytes:
    return mal_find_meta_comment_function.read()


@pytest.fixture
def find_meta_comment_tree(utf8_mal_parser: Parser, find_meta_comment_data: bytes) -> Tree:
    return utf8_mal_parser.parse(find_meta_comment_data)


@pytest.mark.parametrize(
    "point,expected_comments",
    parameters,
)
def test_find_meta_comment_function(
    mal_root_str: str,
    mal_find_meta_comment_function_uri: str,
    find_meta_comment_data: bytes,
    find_meta_comment_tree: Tree,
    point: (int, int),
    expected_comments: list[bytes],
):
    # build the storage (mimicks the file parsing in the server)
    storage = {}

    doc_uri = mal_find_meta_comment_function_uri
    source_encoded = find_meta_comment_data
    tree = find_meta_comment_tree

    storage[doc_uri] = Document(tree, source_encoded, doc_uri)

    # obtain the included files
    root_node = tree.root_node

    captures = run_query(root_node, INCLUDED_FILES_QUERY)
    if "file_name" in captures:
        recursive_parsing(mal_root_str, captures["file_name"], storage, doc_uri, [])

    ###################################

    # get the node
    cursor = tree.walk()
    while cursor.goto_first_child_for_point(point) is not None:
        continue

    # confirm it's an identifier
    assert cursor.node.type == "identifier"

    # we use sets to ensure order does not matter
    comments = [
        x.child_by_field_name("info").text.strip(b'"')
        for x in find_meta_comment_function(cursor.node, cursor.node.text, doc_uri, storage)
    ]

    assert set(comments) == expected_comments
