import pytest

from malls.lsp.enums import DiagnosticSeverity

from ..util import server_output

pytest_plugins = ["tests.fixtures.lsp.publish_diagnostics"]

parameters = [
    ("erroneous_file_client_messages", "mal_erroneous_uri", DiagnosticSeverity.Error),
    (
        "erroenous_include_and_file_with_error_client_messages",
        "mal_file_with_error_uri",
        DiagnosticSeverity.Error,
    ),
    ("change_file_with_error_client_messages", "mal_base_open_uri", DiagnosticSeverity.Error),
]
parameter_ids = ["erroneous_file", "erroneous_include_file", "change_file_with_error"]


@pytest.mark.parametrize(
    "messages_fixture_name,uri_fixture_name,error_level", parameters, ids=parameter_ids
)
def test_open_file(
    request: pytest.FixtureRequest,
    messages_fixture_name: str,
    uri_fixture_name: str,
    error_level: DiagnosticSeverity,
):
    input = request.getfixturevalue(messages_fixture_name)
    uri = request.getfixturevalue(uri_fixture_name)

    # since Document acts inconsistent with URIs
    uri = uri[len("file://") :]

    # send to server
    output, ls, *_ = server_output(input)

    # Ensure LSP stored everything correctly
    assert len(ls.diagnostics) == 1
    assert uri in ls.diagnostics
    assert len(ls.diagnostics[uri]) == 1
    assert ls.diagnostics[uri][0]["severity"] == error_level

    output.close()
