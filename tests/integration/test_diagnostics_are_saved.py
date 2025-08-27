import typing
from pathlib import Path

from malls.lsp.enums import DiagnosticSeverity

from ..util import server_output

# calculate file path of mal files
FILE_PATH = str(Path(__file__).parent.parent.resolve()) + "/fixtures/mal/"
simplified_file_path = FILE_PATH + "main.mal"
included_file_path = FILE_PATH + "file_with_error.mal"


def test_open_file_with_error(
    open_file_with_error: typing.BinaryIO,
):
    # send to server
    output, ls, *_ = server_output(open_file_with_error)

    # Ensure LSP stored everything correctly
    assert len(ls.diagnostics) == 1
    assert len(ls.diagnostics[simplified_file_path]) == 1
    assert ls.diagnostics[simplified_file_path][0]["severity"] == DiagnosticSeverity.Error

    output.close()


def test_open_file_with_include_error(
    open_file_with_include_error: typing.BinaryIO,
):
    # send to server
    output, ls, *_ = server_output(open_file_with_include_error)

    # Ensure LSP stored everything correctly
    assert len(ls.diagnostics) == 1
    assert len(ls.diagnostics[included_file_path]) == 1
    assert ls.diagnostics[included_file_path][0]["severity"] == DiagnosticSeverity.Error

    output.close()


def test_change_file_with_error(
    change_file_with_error: typing.BinaryIO,
):
    # send to server
    output, ls, *_ = server_output(change_file_with_error)

    # Ensure LSP stored everything correctly
    assert len(ls.diagnostics) == 1
    assert len(ls.diagnostics[simplified_file_path]) == 1
    assert ls.diagnostics[simplified_file_path][0]["severity"] == DiagnosticSeverity.Error

    output.close()
