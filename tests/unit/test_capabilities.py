import pytest

import malls.lsp.capabilities as capabilities
from malls.lsp.enums import PositionEncodingKind
from malls.lsp.models import ClientCapabilities

encoding_parameters = [
    # Prefer UTF8 over UTF16 and UTF32
    (
        [PositionEncodingKind.UTF32, PositionEncodingKind.UTF16, PositionEncodingKind.UTF8],
        PositionEncodingKind.UTF8,
    ),
    # Select UTF8 between UTF8, garantueed UTF16, and UTF32
    ([PositionEncodingKind.UTF32, PositionEncodingKind.UTF8], PositionEncodingKind.UTF8),
    # Select UTF8 between UTF8 and UTF16
    ([PositionEncodingKind.UTF16, PositionEncodingKind.UTF8], PositionEncodingKind.UTF8),
    # Select UTF8 if its the only one (including garantueed UTF16)
    ([PositionEncodingKind.UTF8], PositionEncodingKind.UTF8),
    # Default to UTF16 for empty list
    ([], PositionEncodingKind.UTF16),
    # Default to UTF16 when UTF8 is not available
    ([PositionEncodingKind.UTF32], PositionEncodingKind.UTF16),
]
encoding_parameter_ids = [
    "select_utf8_in_utf8_utf16_utf32",
    "select_utf8_in_utf8_utf32",
    "select_utf8_in_utf8_utf16",
    "select_sole_utf8",
    "default_to_utf16_on_empty",
    "default_to_utf16_without_utf8",
]


@pytest.mark.parametrize(
    "encoding_list,expected_encoding", encoding_parameters, ids=encoding_parameter_ids
)
def test_process_encoding(
    encoding_list: list[PositionEncodingKind], expected_encoding: PositionEncodingKind
):
    assert capabilities.process_encoding(encoding_list) == expected_encoding


capabilities_encoding_parameters = [
    (None, PositionEncodingKind.UTF16),
    ({"general": {"positionEncodings": [PositionEncodingKind.UTF32]}}, PositionEncodingKind.UTF16),
    ({"general": {"positionEncodings": []}}, PositionEncodingKind.UTF16),
    ({"general": {"positionEncodings": None}}, PositionEncodingKind.UTF16),
    (
        {"general": {"positionEncodings": [PositionEncodingKind.UTF16, PositionEncodingKind.UTF8]}},
        PositionEncodingKind.UTF8,
    ),
]
capabilities_encoding_parameter_ids = [
    "no_capabilites",
    "utf32_only",
    "empty_position_encodings",
    "no_position_encodings",
    "prefer_utf8",
]


@pytest.mark.parametrize(
    "capabilities_dict,expected_encoding",
    capabilities_encoding_parameters,
    ids=capabilities_encoding_parameter_ids,
)
def test_process_client_capabilities_encoding(
    capabilities_dict: dict | None, expected_encoding: PositionEncodingKind
):
    client_capabilities = ClientCapabilities(**capabilities_dict) if capabilities_dict else None
    server_capabilities = capabilities.process_client_capabilities(client_capabilities)
    assert server_capabilities["positionEncoding"] == expected_encoding


@pytest.mark.skip("Implement when process_client_capabilities does not return consts")
def test_process_client_capabilities():
    pass
