from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_snake
from typing_extensions import TypedDict
from uritools import isuri

base_config = ConfigDict(alias_generator = to_snake)

Integer = Annotated[int,
                    Field(ge=-2^31, le=2^31-1),
                    """Defines an integer number in the range of -2^31 to 2^31 - 1."""]
UInteger = Annotated[Integer,
                     Field(ge=0),
                     """Defines an unsigned integer number in the range of 0 to 2^31 - 1."""]
Uri = Annotated[str,
                AfterValidator(isuri),
                """
                URI’s are transferred as strings. The URI’s format is defined in https://tools.ietf.org/html/rfc3986

                https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#uri
                """]
DocumentUri = Annotated[Uri,
                        """
                        Many of the interfaces contain fields that correspond to the URI of a
                        document. For clarity, the type of such a field is declared as a
                        `DocumentUri`. Over the wire, it will still be transferred as a string, but
                        this guarantees that the contents of that string can be parsed as a valid
                        URI.

                        https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#uri
                        """]

# NOTE: Both BaseModel and TypedDict are used to explicitely support the faster validation method

class CancelParams(BaseModel, TypedDict):
    """
    The base protocol offers support for request cancellation.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#cancelRequest
    """

    id: Integer | str
    """The request id to cancel."""

class ProgressParams[T](BaseModel, TypedDict):
    """
    The base protocol offers also support to report progress in a generic fashion. This mechanism
    can be used to report any kind of progress including work done progress (usually used to report
    progress in the user interface using a progress bar) and partial result progress to support
    streaming of results.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#progress
    """

    token: Integer | str
    """The progress token provided by the client or server."""

    value: T
    """The progress data."""

class RegularExpressionsClientCapabilities(BaseModel, TypedDict):
    engine: str
    """The engine's name."""

    version: str | None
    """The engine's version."""

class Position(BaseModel, TypedDict):
    """
    Position in a text document expressed as zero-based line and zero-based character offset. A
    position is between two characters like an ‘insert’ cursor in an editor. Special values like
    for example -1 to denote the end of a line are not supported.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#position
    """

    line: UInteger
    """Line position in a document (zero-based)."""

    character: UInteger
    """
    Character offset on a line in a document (zero-based). The meaning of this
	offset is determined by the negotiated `PositionEncodingKind`.

	If the character value is greater than the line length it defaults back
	to the line length.
    """

class Range(BaseModel, TypedDict):
    """
    A range in a text document expressed as (zero-based) start and end positions. A range is
    comparable to a selection in an editor. Therefore, the end position is exclusive. If you want
    to specify a range that contains a line including the line ending character(s) then use an end
    position denoting the start of the next line.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#range
    """

    start: Position
    """The range's start position."""

    end: Position
    """The range's end position."""

class TextDocumentItem(BaseModel, TypedDict):
    """
    An item to transfer a text document from the client to the server.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocumentItem
    """

    uri: DocumentUri
    """The text document's URI."""

    language_id: str
    """The text document's language identifier."""

    version: Integer
    """
    The version number of this document (it will increase after each change, including undo/redo).
    """

    text: str
    """The content of the opened text document."""
