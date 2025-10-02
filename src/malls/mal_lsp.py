import logging
import typing

import tree_sitter_mal as ts_mal
from pylsp_jsonrpc.dispatchers import MethodDispatcher, _method_to_string
from pylsp_jsonrpc.endpoint import Endpoint
from pylsp_jsonrpc.streams import JsonRpcStreamReader, JsonRpcStreamWriter
from tree_sitter import Language, Parser

from .lsp import enums, models
from .lsp.classes import Document
from .lsp.enums import ErrorCodes, MarkupKind, PositionEncodingKind, TraceValue
from .lsp.fsm import LifecycleFSM
from .lsp.utils import (
    get_completion_list,
    get_hover_info,
    path_to_uri,
    recursive_parsing,
    send_diagnostics,
    uri_to_path,
)
from .ts.utils import (
    INCLUDED_FILES_QUERY,
    find_symbol_definition,
    position_to_node,
    query_for_error_nodes,
    run_query,
    tree_sitter_to_lsp_position,
)

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
        self.__diagnostics = {}

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
            "textDocumentSync": {
                "openClose": True,
                "change": 1,
            },
            "definitionProvider": True,
            "completionProvider": {},
            "hoverProvider": True,
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

    @property
    def files(self) -> dict:
        return self.__files

    @property
    def diagnostics(self) -> dict:
        return self.__diagnostics

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
                "serverInfo": {"name": "mal-language-server"},
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

    def m_text_document__did_open(self, **params: dict | None) -> None:
        """
        This function will handle the notification that a new text document
        was open. For that, we must parse the given file and included files
        as well, since they might contain info worth providing to the user
        """

        # validate params
        instance = models.DidOpenTextDocumentParams(**params)
        # obtain the document URI and text
        doc_uri = uri_to_path(instance.textDocument.uri)
        doc_text = instance.textDocument.text

        # if the file has been parsed (e.g. was included by another file)
        # we do not need to parse it again
        if doc_uri in self.__files.keys():
            # the document was already parsed but had errors
            if doc_uri in self.__diagnostics:
                send_diagnostics(self.__diagnostics[doc_uri], doc_uri, self.__endpoint)
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
        self.__files[doc_uri] = Document(tree, source_encoded, doc_uri)

        # find all possible errors
        query_for_error_nodes(tree, source_encoded, doc_uri, self.__diagnostics)
        if doc_uri in self.__diagnostics:
            # the document was properly opened but had errors
            send_diagnostics(self.__diagnostics[doc_uri], doc_uri, self.__endpoint)

        # obtain the included files
        root_node = tree.root_node

        captures = run_query(root_node, INCLUDED_FILES_QUERY)

        if captures:  # If there are included files, start recursive parsing
            recursive_parsing(
                path_prec, captures["file_name"], self.__files, doc_uri, self.__diagnostics
            )

        # with the opened file and included files parsed, we are done
        return

    def m_text_document__did_change(self, **params: dict | None) -> None:
        """
        This function will process changes to files. To do this, the source
        code must be edited, TreeSitter alerted of the location of the changes
        and finally the code must be reparsed.
        """

        # Obtain text document
        textDocument = models.DidChangeTextDocumentParams(**params)
        doc_uri = uri_to_path(textDocument.text_document.uri)
        document = self.__files[doc_uri]

        # There could be various changes, so we need to iterate over them
        for change in textDocument.content_changes:
            try:
                changed_range = change.range
                text = change.text.encode()
                document.execute_changes(changed_range, text)
            except Exception:
                text = change.text.encode()  # whole file change
                document.change_whole_file(text)

        # after changing and reparsing the file, find all possible errors
        query_for_error_nodes(document.tree, document.text, doc_uri, self.__diagnostics)
        if doc_uri in self.__diagnostics:
            # the document was properly changed but had errors
            send_diagnostics(self.__diagnostics[doc_uri], doc_uri, self.__endpoint)

    def m_text_document__definition(self, **params: dict | None) -> None:
        # validate parameters
        definition = models.DefinitionParams(**params) if params else None
        if definition is None:
            return None

        # obtain document uri and position
        document_uri = uri_to_path(definition.text_document.uri)
        position_lsp = definition.position

        # obtain node and position in TS from the LSP position
        # (we assume that the document is in the open/parsed files)
        document = self.__files[document_uri]
        node, point, symbol = position_to_node(document.tree, document.text, position_lsp)

        if node.type != "identifier":
            return None  # we only care about identifiers

        # call the method that will find the definition
        result_node, result_doc = find_symbol_definition(node, symbol, document_uri, self.__files)

        # if no node was found
        if result_node is None:
            return None

        # otherwise, we have to convert back to LSP positions and return the
        # results to the user
        result_doc = self.__files[result_doc]
        result_lsp_position_start = tree_sitter_to_lsp_position(
            result_doc.text, result_node.start_point
        )
        result_lsp_position_end = tree_sitter_to_lsp_position(
            result_doc.text, result_node.end_point
        )

        # build response
        result_range = models.Range(start=result_lsp_position_start, end=result_lsp_position_end)
        result_uri = path_to_uri(result_doc.uri)

        return {
            "uri": result_uri,
            "range": {
                "start": {
                    "line": result_range.start.line,
                    "character": result_range.start.character,
                },
                "end": {
                    "line": result_range.end.line,
                    "character": result_range.end.character,
                },
            },
        }

    def m_text_document__completion(self, **params: dict | None) -> None:
        # validate parameters
        completion = models.CompletionParams(**params) if params else None
        if completion is None:
            return None  # parameters are wrong

        # obtain relevant parameters
        doc_uri = uri_to_path(completion.text_document.uri)
        position = completion.position

        # get completion list
        completion_list = get_completion_list(self.__files[doc_uri], position)

        # For now, the list is complete, so we can just return it.
        # From the documentation:
        # `If a CompletionItem[] is provided it is interpreted to
        # be complete. So it is the same as { isIncomplete: false, items }`
        return completion_list

    def m_text_document__hover(self, **params: dict | None) -> None | dict:
        # validate parameters
        hover = models.HoverParams(**params) if params else None
        if hover is None:
            return None  # parameters are wrong

        # obtain relevant parameters
        doc_uri = uri_to_path(hover.text_document.uri)
        position = hover.position

        # get completion list
        hover_content = get_hover_info(self.__files[doc_uri], position, self.__files)

        return {
            "contents": {
                "kind": MarkupKind.Markdown,
                "value": hover_content,
            }
        }
