from .enums import PositionEncodingKind, TextDocumentSyncKind
from .models import ClientCapabilities


def process_encoding(encodings: list[PositionEncodingKind]):
    # Prefer UTF8 when available
    if PositionEncodingKind.UTF8 in encodings:
        return PositionEncodingKind.UTF8
    else:
        return PositionEncodingKind.UTF16


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
    if client_capabilities is not None:
        if client_capabilities.general is not None:
            general = client_capabilities.general
            if general.position_encodings is not None:
                capabilities["positionEncoding"] = process_encoding(general.position_encodings)
    return capabilities
