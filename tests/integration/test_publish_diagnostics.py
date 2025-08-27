import typing

from malls.lsp.enums import DiagnosticSeverity

from ..util import get_lsp_json, server_output

pytest_plugins = ["tests.fixtures.lsp.publish_diagnostics"]


def test_diagnostics_when_opening_file_with_error(erroneous_file_client_messages: typing.BinaryIO):
    # send to server
    output, ls, *_ = server_output(erroneous_file_client_messages)

    # Ensure LSP stored everything correctly

    output.seek(0)
    response = get_lsp_json(output)
    response = get_lsp_json(output)

    assert "textDocument/publishDiagnostics" in response["method"]
    params = response["params"]
    assert len(params["diagnostics"]) == 1

    start_point = params["diagnostics"][0]["range"]["start"]
    assert (start_point["line"], start_point["character"]) == (4, 13)
    assert params["diagnostics"][0]["severity"] == DiagnosticSeverity.Error

    output.close()


def test_diagnostics_when_opening_file_with_include_error(
    erroneous_include_file_client_messages: typing.BinaryIO,
):
    # send to server
    output, ls, *_ = server_output(erroneous_include_file_client_messages)

    output.seek(0)
    get_lsp_json(output)

    # ensure buffer has no more content
    # (diagnostic should not be sent because the problematic
    # file was not opened)
    current_pos = output.tell()
    output.seek(0, 2)
    assert current_pos == output.tell()

    output.close()


def test_diagnostics_when_opening_file_with_include_error_and_opening_bad_file(
    erroenous_include_and_file_with_error_client_messages: typing.BinaryIO,
):
    # send to server
    output, ls, *_ = server_output(erroenous_include_and_file_with_error_client_messages)

    output.seek(0)
    response = get_lsp_json(output)
    response = get_lsp_json(output)

    # this time the problematic file was opened, so there should be a diagnostic
    assert "textDocument/publishDiagnostics" in response["method"]
    params = response["params"]
    assert len(params["diagnostics"]) == 1

    start_point = params["diagnostics"][0]["range"]["start"]
    assert (start_point["line"], start_point["character"]) == (0, 0)
    assert params["diagnostics"][0]["severity"] == DiagnosticSeverity.Error

    output.close()


def test_diagnostics_when_changing_file_with_error(
    change_file_with_error_client_messages: typing.BinaryIO,
):
    # send to server
    output, ls, *_ = server_output(change_file_with_error_client_messages)

    output.seek(0)
    response = get_lsp_json(output)
    response = get_lsp_json(output)

    # this time the problematic file was opened, so there should be a diagnostic
    assert "textDocument/publishDiagnostics" in response["method"]
    params = response["params"]
    assert len(params["diagnostics"]) == 1

    start_point = params["diagnostics"][0]["range"]["start"]
    assert (start_point["line"], start_point["character"]) == (5, 17)
    assert params["diagnostics"][0]["severity"] == DiagnosticSeverity.Error

    output.close()
