from pydantic import BaseModel
from typing_extensions import TypedDict


class CancelParams(BaseModel, TypedDict):
    """
    The base protocol offers support for request cancellation.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#cancelRequest
    """

    id: int | str
    """The request id to cancel."""
