import logging
import typing

from pylsp_jsonrpc.dispatchers import MethodDispatcher
from pylsp_jsonrpc.endpoint import Endpoint
from pylsp_jsonrpc.streams import JsonRpcStreamReader, JsonRpcStreamWriter

log = logging.getLogger(__name__)
MAL_FILETYPES = (".mal",)


def start_fileio_server(in_file: typing.BinaryIO, out_file: typing.BinaryIO) -> None:
    log.info("Starting MAL LSP IO language server.")


class MALLSPServer(MethodDispatcher):
    def __init__(
        self, input: typing.BinaryIO | None = None, output: typing.BinaryIO | None = None
    ) -> None:
        self.__jsonrpc_stream_reader = JsonRpcStreamReader(input) if input else None
        self.__jsonrpc_stream_writer = JsonRpcStreamWriter(output) if output else None

        self.__endpoint = Endpoint(self, self.__jsonrpc_stream_writer.write)
