import typing

from malls.lsp.enums import PositionEncodingKind

from ..util import get_lsp_json, server_output


def test_encoding_capability_simple(encoding_capability_check_in: typing.BinaryIO):
    output, ls, *_ = server_output(encoding_capability_check_in)

    # the test and server share the same buffer,
    # so we must reset the cursor
    output.seek(0)

    response = get_lsp_json(output)

    # Ensure encoding defaults to UTF16 if not specified by the client
    # https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#clientCapabilities
    assert response["result"]["capabilities"]["positionEncoding"] == PositionEncodingKind.UTF16
