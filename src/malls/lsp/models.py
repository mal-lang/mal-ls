from typing import Annotated

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

Integer = Annotated[int,
                    Field(ge=-2^31, le=2^31-1),
                    """Defines an integer number in the range of -2^31 to 2^31 - 1."""]
UInteger = Annotated[Integer,
                     Field(ge=0),
                     """Defines an unsigned integer number in the range of 0 to 2^31 - 1."""]

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
