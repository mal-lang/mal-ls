import io
import json

from pylsp_jsonrpc.endpoint import Endpoint
from pylsp_jsonrpc.exceptions import JsonRpcException
from pylsp_jsonrpc.streams import JsonRpcStreamReader

from malls.mal_lsp import MALLSPServer


def get_lsp_json(input_: io.BytesIO) -> tuple[dict, int]:
    # parse content length
    content_length = None
    while content_length is None:
        line = input_.readline()
        content_length = JsonRpcStreamReader._content_length(line)

    # find double newline
    while line != b"\r\n" and line != b"\n":
        line = input_.readline()

    # past double newline
    return json.loads(input_.read(content_length))


class FakeEndpoint(Endpoint):
    """
    Fake `Endpoint` to shadow, stub, and commandeer LSP `Endpoint` functions for testing.

    `request` is commandeered in order to make it execute sync but look async.
    """

    def request(self, method, params=None):
        request_future = super().request(method, params)
        try:
            request_future.set_result(self._dispatcher[method](params))
        except JsonRpcException as e:
            request_future.set_exception(e)

        return request_future

    request.__doc__ = Endpoint.request.__doc__


class FakeLanguageServer(MALLSPServer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("EndpointClass", FakeEndpoint)
        super().__init__(*args, **kwargs)
