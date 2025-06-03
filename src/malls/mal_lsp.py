import logging
import typing

from pylsp_jsonrpc.dispatchers import MethodDispatcher
from pylsp_jsonrpc.endpoint import Endpoint
from pylsp_jsonrpc.streams import JsonRpcStreamReader, JsonRpcStreamWriter

from .lsp.enums import ErrorCodes
from .lsp.fsm import LifecycleFSM

log = logging.getLogger(__name__)
MAL_FILETYPES = (".mal",)


def start_fileio_server(in_file: typing.BinaryIO, out_file: typing.BinaryIO) -> None:
    log.info("Starting MAL IO language server.")
    server = MALLSPServer(in_file, out_file)
    server.start()


class MALLSPServer(MethodDispatcher):
    def __init__(
        self, input: typing.BinaryIO | None = None, output: typing.BinaryIO | None = None
    ) -> None:
        self.__jsonrpc_stream_reader = JsonRpcStreamReader(input) if input else None
        self.__jsonrpc_stream_writer = JsonRpcStreamWriter(output) if output else None

        self.__endpoint = Endpoint(self, self.__jsonrpc_stream_writer.write)

        self.__encoding = 'utf-16'
        self.__lifecycle = LifecycleFSM()

    def start(self) -> None:
        """Starts the language server."""
        log.info("Starting MAL LSP language server.")
        self.__jsonrpc_stream_reader.listen(self.__endpoint.consume)

    # leave capabilities as dict for now, replace with explicit class/type later
    def capabilities(self, client_capabilities: dict | None = None):
        capabilities = {}
        log.debug("Server capabilities: %s", capabilities)
        return capabilities

    def __getitem__(self, item):
        """Override to ensure that correct initialize/d shutdown/exit transitions are done."""
        if self.__lifecycle.may_accept(item):
            self.__lifecycle.accepts(item)
        else:
            item = "invalid_request_at_" + self.__lifecycle.current_state
        try:
            return super().__getitem__(item)
        except Exception as e:
            # Log and rethrow, cannot do anything if the method isn't known
            log.error(f"Error attempting to reach method `{item}`:", str(e))
            raise e

    @property
    def state(self) -> LifecycleFSM:
        return self.__lifecycle

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

    def m_initialized(self, *args, **kwargs) -> None:
        log.debug("Client initialized with parameters %s %s", args, kwargs)

    def m_shutdown(self, **kwargs) -> None:
        log.info("Received shutdown request.")

    @staticmethod
    # leave return type as dict for now, replace with explicit class/type later
    def __invalid_request_at_lifecycle(
            warning: str,
            message: str,
            error: ErrorCodes = ErrorCodes.InvalidRequest) -> dict:
        log.warning(warning)
        return {
            "error": {
                "code": error,
                "message": message,
            }
        }


    def m_invalid_request_at_start(self, **kwargs):
        return MALLSPServer.__invalid_request_at_lifecycle(
            warning="Received non-initialize request before initialized.",
            message="Non-`initialize` as first request is not valid."
        )

    def m_invalid_request_at_initialize(self, **kwargs):
        return MALLSPServer.__invalid_request_at_lifecycle(
            warning="Received request before initialized.",
            message="Must wait for `initalized` notification before other requests."
        )

    def m_invalid_request_at_initialized(self, **kwargs):
        return MALLSPServer.__invalid_request_at_lifecycle(
            warning="Received errenous request when initalized.",
            message=("Only feature methods and `shutdown` are allowed after `initialized`"
                     "notification.")
        )

    def m_invalid_request_at_shutdown(self, **kwargs):
        return MALLSPServer.__invalid_request_at_lifecycle(
            warning="Received non-exit request after shutdown.",
            message="Non-`exit` requests after `shutdown` are not valid."
        )

    def m_invalid_request_at_exit(self, **kwargs):
        return MALLSPServer.__invalid_request_at_lifecycle(
            warning="Received request after exit.",
            message="Requests after `exit` are not valid."
        )

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
