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
