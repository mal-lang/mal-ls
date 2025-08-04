import logging
import os
import typing
from pathlib import Path
from urllib.parse import urlparse

import tree_sitter_mal as ts_mal
from pylsp_jsonrpc.dispatchers import MethodDispatcher, _method_to_string
from pylsp_jsonrpc.endpoint import Endpoint
from pylsp_jsonrpc.streams import JsonRpcStreamReader, JsonRpcStreamWriter
from tree_sitter import Language, Parser

from .lsp import enums, models
from .lsp.classes import Document
from .lsp.enums import ErrorCodes, PositionEncodingKind, TraceValue
from .lsp.fsm import LifecycleFSM
from .ts.utils import INCLUDED_FILES_QUERY, run_query

log = logging.getLogger(__name__)
MAL_FILETYPES = (".mal",)
MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)


class MALLSPException(Exception):
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

        self.__files = {}

    def start(self) -> None:
        """Starts the language server."""
        log.info("Starting MAL LSP language server.")
        self.__jsonrpc_stream_reader.listen(self.__endpoint.consume)

    def _process_encoding(self, encodings: list[PositionEncodingKind]):
        # According to documentation, if utf-16 is missing, the server should
        # assume that this encoding is supported and should be used.
        #
        # Therefore, only if the UTF-16 is present can we choose another
        # encoding
        #
        # TODO decide which encoding to choose
        if PositionEncodingKind.UTF16 in encodings:
            # TODO change encoding
            # self.__encoding = ???
            pass

    # Auxiliary method to process and react to client capabilities
    def _process_client_capabilities(self, client_capabilities: models.ClientCapabilities) -> None:
        if client_capabilities.general:
            general = client_capabilities.general
            if general.position_encodings:
                self._process_encoding(general.position_encodings)

    # leave capabilities as dict for now, replace with explicit class/type later
    def capabilities(self, client_capabilities: models.ClientCapabilities | None = None):
        if client_capabilities:
            self._process_client_capabilities(client_capabilities)

        capabilities = {
            "positionEncoding": self.__encoding,
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
    def trace_value(self) -> TraceValue:
        return self.__trace_value

    def files(self) -> dict:
        return self.__files

    # Helper function to change the traceValue.
    # Log an error if the traceValue is not recognized.
    def _change_trace_value(self, new_trace_value: enums.TraceValue) -> None:
        match new_trace_value:
            case enums.TraceValue.Off | enums.TraceValue.Messages | enums.TraceValue.Verbose:
                self.__trace_value = new_trace_value
            case _:
                error_msg = (
                    f"Unrecognized trace value: `{new_trace_value}`."
                    " Options are: `off`, `messages` and `verbose`."
                )
                log.error(error_msg)
                raise MALLSPException(ErrorCodes.InvalidParams, error_msg)

        log.info(f"Updating trace value to: `{new_trace_value}`")

    # This method is to be incrementally increased by adding
    # processing capabilities for each of the initialize parameters
    def _process_initialize_parameters(self, parameters: models.InitializeParams):
        if parameters.trace:
            self._change_trace_value(parameters.trace)

    # leave capabilities and response as dict for now, replace with explicit class/type later
    def m_initialize(self, **params: dict | None) -> dict:
        parameters = models.InitializeParams(**params) if params else None
        log.info("Initializing server with parameters: %s", parameters)

        try:
            if parameters:
                self._process_initialize_parameters(parameters)

            return {
                "capabilities": self.capabilities(parameters.capabilities),
                "serverInfo": {"name": "mal-ls"},
            }
        except MALLSPException as e:
            return MALLSPServer.__respond_with_error(e.error_msg, e.code)

    def m_initialized(self, *args, **kwargs) -> None:
        log.debug("Client initialized with parameters %s %s", args, kwargs)

    def m_shutdown(self, **kwargs) -> None:
        log.info("Received shutdown request.")

    @staticmethod
    def __respond_with_error(error_msg: str, error_code: int) -> dict:
        return {
            "error": {
                "code": error_code,
                "message": error_msg,
            }
        }

    @staticmethod
    # leave return type as dict for now, replace with explicit class/type later
    def __invalid_request_at_lifecycle(
        warning: str, message: str, error: ErrorCodes = ErrorCodes.InvalidRequest
    ) -> dict:
        log.warning(warning)
        return MALLSPServer.__respond_with_error(message, error)

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
        if self.trace_value != TraceValue.Off:
            params = {"message": "Exiting language server"}
            if self.trace_value == TraceValue.Verbose:
                params["verbose"] = "Verbose example"  # placeholder
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

    def m___set_trace(self, **params: dict | None) -> None:
        # For a notification, there is no response,
        # even if there is an error, so the function
        # shall just return
        parameters = models.SetTraceParams(**params) if params else None
        if parameters:
            try:
                self._change_trace_value(parameters.value)
            finally:
                return

    def _uri_to_path(self, uri: str) -> Path:
        """
        Auxiliary method to convert file:// URI back to filesystem path
        """

        parsed = urlparse(uri).path

        if os.name == "nt":  # handle Windows
            parsed = parsed[1:]
        return parsed

    def _recursive_parsing(self, uri_prec: str, captures: dict) -> None:
        """
        Auxiliary method to parse included files recursively
        """

        while captures:
            # build file path
            file_name = uri_prec + captures.pop(0).text.decode().strip('"')

            # if the file has already been processed, ignore it
            # (this can happen if file A was opened with a didOpen notification
            # and then file B which extends file A is also opened. By logical order,
            # A was parsed already, so we do not need to do it, since it hasn't changed)

            if file_name in self.__files:
                continue
            if not Path(file_name).exists():
                continue  # file has not been created yet, so we just ignore it

            # otherwise, parse it
            with open(file_name, "rb") as file:
                source = file.read()

            tree = PARSER.parse(source)
            root_node = tree.root_node

            # save parsed file
            self.__files[file_name] = Document(tree, source)

            # check if there are other includes to process
            new_captures = run_query(root_node, INCLUDED_FILES_QUERY)

            # if there are new includes, add them to the list
            if new_captures:
                captures.extend(new_captures["file_name"])

        return

    def m_text_document__did_open(self, **params: dict | None) -> None:
        """
        This function will handle the notification that a new text document
        was open. For that, we must parse the given file and included files
        as well, since they might contain info worth providing to the user
        """

        # obtain the document URI and text
        doc_uri = self._uri_to_path(params["textDocument"]["uri"])
        doc_text = params["textDocument"]["text"]

        # if the file has been parsed (e.g. was included by another file)
        # we do not need to parse it again
        if doc_uri in self.__files:
            return

        # otherwise, parse it
        source_encoded = doc_text.encode()
        tree = PARSER.parse(source_encoded)

        # The given file might include other files, which must also
        # be parsed, as they could contain information that will be
        # queried

        # obtain general URI of files
        path_prec = doc_uri.rsplit("/", 1)[0] + "/"

        # save parsed file
        self.__files[doc_uri] = Document(tree, source_encoded)

        # obtain the included files
        root_node = tree.root_node

        captures = run_query(root_node, INCLUDED_FILES_QUERY)

        if captures:  # If there are included files, start recursive parsing
            self._recursive_parsing(path_prec, captures["file_name"])

        # with the opened file and included files parsed, we are done
        return
