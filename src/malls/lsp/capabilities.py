from .enums import PositionEncodingKind, TextDocumentSyncKind
from .models import ClientCapabilities


def process_encoding(encodings: list[PositionEncodingKind] | None):
    # The default, and always supported, option is UTF-16
    if encodings is None or PositionEncodingKind.UTF8 not in encodings:
        return PositionEncodingKind.UTF16
    else:
        return PositionEncodingKind.UTF8

# Auxiliary method to process and react to client capabilities
def process_client_capabilities(client_capabilities: ClientCapabilities | None) -> dict:
    capabilities = {
        "positionEncoding": PositionEncodingKind.UTF16,
        "textDocumentSync": {
            "openClose": True,
            "change": TextDocumentSyncKind.FULL,
            },
        "definitionProvider": True,
        "completionProvider": {},
    }
    if client_capabilities:
        if client_capabilities.general:
            general = client_capabilities.general
            if general.position_encodings:
                capabilities["positionEncoding"] = process_encoding(general.position_encodings)
    return capabilities
