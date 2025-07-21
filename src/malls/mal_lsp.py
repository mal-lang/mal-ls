import logging
import typing

from pylsp_jsonrpc.dispatchers import MethodDispatcher, _method_to_string
from pylsp_jsonrpc.endpoint import Endpoint
from pylsp_jsonrpc.streams import JsonRpcStreamReader, JsonRpcStreamWriter

from .lsp.enums import ErrorCodes, TraceValue, PositionEncodingKind
from .lsp.fsm import LifecycleFSM

log = logging.getLogger(__name__)
MAL_FILETYPES = (".mal",)

class MALLSPEXCEPTION(Exception):
    def __init__(self, code, message):
        self.code = code
        self.error_msg = message
        super().__init__(f"Error {code}: {message}") 

def start_fileio_server(in_file: typing.BinaryIO, out_file: typing.BinaryIO) -> None:
    log.info("Starting MAL IO language server.")
    server = MALLSPServer(in_file, out_file)
    server.start()


class MALLSPServer(MethodDispatcher):
    def __init__(
        self,
        input: typing.BinaryIO | None = None,
        output: typing.BinaryIO | None = None,
        JsonRpcReaderClass=JsonRpcStreamReader,
        JsonRpcWriterClass=JsonRpcStreamWriter,
        EndpointClass: Endpoint = Endpoint,
        LifecycleClass: LifecycleFSM = LifecycleFSM,
    ) -> None:
        self.__jsonrpc_stream_reader = JsonRpcReaderClass(input) if input else None
        self.__jsonrpc_stream_writer = JsonRpcWriterClass(output) if output else None

        self.__endpoint = EndpointClass(self, self.__jsonrpc_stream_writer.write)

        self.__encoding = "utf-16"
        self.__lifecycle = LifecycleClass()

        # By default, the value is Off
        self.__trace_value = TraceValue.Off

    def start(self) -> None:
        """Starts the language server."""
        log.info("Starting MAL LSP language server.")
        self.__jsonrpc_stream_reader.listen(self.__endpoint.consume)

    def _process_encoding(self, encodings: PositionEncodingKind):
        # According to documentation, if utf-16 is missing, the server should
        # assume that this encoding is supported and should be used.
        #
        # Therefore, only if the UTF-16 is present can we choose another
        # encoding
        #
        # TODO decide which encoding to choose
        if (PositionEncodingKind.UTF16 in encodings):
            # TODO change encoding
            # self.__encoding = ???
            pass

    # Auxiliary method to process and react to client capabilities
    def _process_client_capabilities(self, capabilities: dict):
        if ('general' in client_capabilities):
            general = client_capabilities['general']
            if ('positionEncodings' in general):
                self._process_encoding(general['positionEncodings'])
        return 

    # leave capabilities as dict for now, replace with explicit class/type later
    def capabilities(self, client_capabilities: dict | None = None):

        if client_capabilities:
            self._process_client_capabilities(capabilities)

        capabilities = {
            'positionEncoding': self.__encoding,
        }
        log.debug("Server capabilities: %s", capabilities)
        return capabilities

    def __getitem__(self, item):
        """Override to ensure that correct initialize/d shutdown/exit transitions are done."""
        if self.__lifecycle.may_accept(item):
            self.__lifecycle.accepts(item)
        else:
            item = "invalid_request_at_" + self.__lifecycle.current_state
        try:
            return super().__getitem__(_method_to_string(item))
        except Exception as e:
            # Log and rethrow, cannot do anything if the method isn't known
            log.error(f"Error attempting to reach method `{item}`:", str(e))
            raise e

    @property
    def state(self) -> LifecycleFSM:
        return self.__lifecycle

    @property
    def traceValue(self) -> TraceValue:
        return self.__trace_value

    # Helper function to change the traceValue.
    # Log an error if the traceValue is not recognized.
    def _change_trace_value(self, new_trace_value: str) -> None:
        match (new_trace_value):
            case 'off':
                self.__trace_value = TraceValue.Off
            case 'messages':
                self.__trace_value = TraceValue.Messages
            case 'verbose':
                self.__trace_value = TraceValue.Verbose
            case _:
                error_msg = f'Unrecognized trace value: `{new_trace_value}`. Options are: `off`, `messages` and `verbose`.'
                log.error(error_msg)
                raise MALLSPEXCEPTION(ErrorCodes.InvalidParams, error_msg)

        log.info(f"Updating trace value to: `{new_trace_value}`")

    # This method is to be incrementally increased by adding
    # processing capabilities for each of the initialize parameters
    def _process_initialize_parameters(self, **kwargs):
        if ('trace' in kwargs):
            self._change_trace_value(kwargs['trace'])

    # leave capabilities and response as dict for now, replace with explicit class/type later
    def m_initialize(
        self, processId: int | None = None, rootUri: str | None = None, **kwargs
    ) -> dict:
        log.info("Initializing server with parameters: %s %s", processId, rootUri)
        log.debug("Defered server parameters: %s", kwargs)

        try:
            if (kwargs):
                self._process_initialize_parameters(**kwargs)

            return {
                "capabilities": self.capabilities(kwargs.get("capabilities")),
                "serverInfo": {"name": "mal-ls"},
            }
        except MALLSPEXCEPTION as e:
            return self.__respond_with_error(e.error_msg,e.code)

    def m_initialized(self, *args, **kwargs) -> None:
        log.debug("Client initialized with parameters %s %s", args, kwargs)

    def m_shutdown(self, **kwargs) -> None:
        log.info("Received shutdown request.")

    @staticmethod
    # leave return type as dict for now, replace with explicit class/type later
    def __invalid_request_at_lifecycle(
        warning: str, message: str, error: ErrorCodes = ErrorCodes.InvalidRequest
    ) -> dict:
        log.warning(warning)
        return {
            "error": {
                "code": error,
                "message": message,
            }
        }

    # TODO maybe join with __invalid_request_at_lifecycle
    def __respond_with_error(self, error_msg: str, error_code: int) -> dict:
        return {
            "error": {
                "code": error_code,
                "message": error_msg,
            }
        }

    def m_invalid_request_at_start(self, **kwargs):
        return MALLSPServer.__invalid_request_at_lifecycle(
            warning="Received non-initialize request before initialized.",
            message="Non-`initialize` as first request is not valid.",
        )

    def m_invalid_request_at_initialize(self, **kwargs):
        return MALLSPServer.__invalid_request_at_lifecycle(
            warning="Received request before initialized.",
            message="Must wait for `initalized` notification before other requests.",
        )

    def m_invalid_request_at_initialized(self, **kwargs):
        return MALLSPServer.__invalid_request_at_lifecycle(
            warning="Received errenous request when initalized.",
            message=(
                "Only feature methods and `shutdown` are allowed after `initialized`notification."
            ),
        )

    def m_invalid_request_at_shutdown(self, **kwargs):
        return MALLSPServer.__invalid_request_at_lifecycle(
            warning="Received non-exit request after shutdown.",
            message="Non-`exit` requests after `shutdown` are not valid.",
        )

    def m_invalid_request_at_exit(self, **kwargs):
        return MALLSPServer.__invalid_request_at_lifecycle(
            warning="Received request after exit.", message="Requests after `exit` are not valid."
        )

    def m_exit(self, **kwargs) -> None:
        
        # Example of notification message
            
        # Only notify if traces are on
        if (self.traceValue != TraceValue.Off):
            params = {'message':'Exiting language server'}
            if self.traceValue == TraceValue.Verbose:
                params['verbose'] = 'Verbose example'  # placeholder
            self.__endpoint.notify("exit", params)

        log.info("Exiting language server.")
        self.__endpoint.shutdown()
        log.info("Endpoint shut down.")
        if self.__jsonrpc_stream_reader:
            self.__jsonrpc_stream_reader.close()
            log.info("JSON RPC reader closed.")
        if self.__jsonrpc_stream_writer:
            self.__jsonrpc_stream_writer.close()
            log.info("JSON RPC writer closed.")

    def m___set_trace(self, **kwargs):
        # For a notification, there is no response,
        # even if there is an error, so the function
        # shall just return
        if ('value' in kwargs):
            try:
                self._change_trace_value(kwargs['value'])
            finally:
                return
