import typing

import pytest
from tree_sitter import Tree

from ..util import server_output

pytest_plugins = ["tests.fixtures.lsp.did_open_text_document_notification"]

parameters = ["base_open", "base_open_file_with_fake_include", "base_open_with_included_file"]


@pytest.mark.parametrize("file", parameters, ids=parameters)
def test_open_file(request: pytest.FixtureRequest, file: str):
    file_fixture: typing.BinaryIO = request.getfixturevalue(f"{file}_client_messages")
    uri_fixture: str = request.getfixturevalue(f"mal_{file}_uri")

    # send to server
    output, ls, *_ = server_output(file_fixture)
    # since Document acts inconsistent with URIs
    uri_fixture = uri_fixture[len("file://") :]

    # Ensure LSP stored everything correctly
    assert uri_fixture in ls.files
    assert type(ls.files[uri_fixture].tree) is Tree

    output.close()
