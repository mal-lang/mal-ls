import logging
import typing

from pylsp_jsonrpc.dispatchers import MethodDispatcher
from pylsp_jsonrpc.endpoint import Endpoint
from pylsp_jsonrpc.streams import JsonRpcStreamReader, JsonRpcStreamWriter

from .lsp.enums import ErrorCodes

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

        self.__encoding = 'utf-16'
        self.__shutdown = False

    def start(self) -> None:
        """Starts the language server."""
        log.info("Starting MAL LSP language server.")
        self.__jsonrpc_stream_reader.listen(self.__endpoint.consume)

    # leave capabilities as dict for now, replace with explicit class/type later
    def capabilities(self, client_capabilities: dict | None = None):
        capabilities = {}
        log.debug("Server capabilities: %s", capabilities)
        return capabilities

    # leave capabilities and response as dict for now, replace with explicit class/type later
    def m_initialize(
            self,
            processId: int | None = None,
            rootUri: str | None = None,
            **kwargs) -> dict:
        log.info(
            "Initializing server with parameters: %s %s",
            processId,
            rootUri)
        log.debug(
            "Defered server parameters: %s",
            kwargs)

        return {
            "capabilities": self.capabilities(kwargs.get("capabilities")),
            "serverInfo": {
                "name": "mal-ls"
            }
        }

    def m_initialized(*args, **kwargs) -> None:
        log.debug("Initialized with parameters %s %s", args, kwargs)

    def m_shutdown(self, **kwargs) -> None:
        log.info("Received shutdown request.")
        self.__shutdown = True

    def m_invalid_request_after_shutdown(self, **kwargs):
        log.warn("Received request after shutdown.")
        return {
            "error": {
                "code": ErrorCodes.InvalidRequest,
                "message": "Requests after `shutdown` are not valid.",
            }
        }

    def m_exit(self, **kwargs) -> None:
        log.info("Exiting language server.")
        self.__endpoint.shutdown()
        log.info("Endpoint shut down.")
        if self.__jsonrpc_stream_reader:
            self.__jsonrpc_stream_reader.close()
            log.info("JSON RPC reader closed.")
        if self.__jsonrpc_stream_writer:
            self.__jsonrpc_stream_writer.close()
            log.info("JSON RPC writer closed.")
