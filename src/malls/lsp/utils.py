import logging
import os
from pathlib import Path

from pylsp_jsonrpc.endpoint import Endpoint
import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser
from uritools import urisplit

from ..ts.utils import INCLUDED_FILES_QUERY, query_for_error_nodes, run_query
from .classes import Document

MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)

log = logging.getLogger(__name__)


def uri_to_path(uri: str) -> Path:
    """
    Auxiliary method to convert file:// URI back to filesystem path
    """

    scheme, authority, path_component, query, fragment = urisplit(uri)

    if os.name == "nt":  # handle Windows
        path_component = path_component[1:]
    return path_component


def recursive_parsing(
    uri_prec: str, captures: list, storage: dict, cur_file: str, diagnostics_storage: list
) -> None:
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

        if file_name in storage:
            continue
        if not Path(file_name).exists():
            continue  # file has not been created yet, so we just ignore it

        # otherwise, parse it
        with open(file_name, "rb") as file:
            source = file.read()

        tree = PARSER.parse(source)

        # save parsed file
        storage[file_name] = Document(tree, source, file_name)

        # find all possible errors
        query_for_error_nodes(tree, source, file_name, diagnostics_storage)

        # save as included file
        storage[cur_file].included_files.append(storage[file_name])

    for included_file_document in storage[cur_file].included_files:
        # check if there are other includes to process
        included_file_uri = included_file_document.uri
        included_file_node = included_file_document.tree.root_node
        new_captures = run_query(included_file_node, INCLUDED_FILES_QUERY)
        if new_captures:
            recursive_parsing(
                uri_prec, new_captures["file_name"], storage, included_file_uri, diagnostics_storage
            )

    return storage


def path_to_uri(filepath: str) -> str:
    """
    Converts a native filesystem path to a file:// URI.
    """
    path_obj = Path(filepath)

    absolute_path_obj = path_obj.resolve()

    return absolute_path_obj.as_uri()


def send_diagnostics(diagnostics: list, file_uri: str, endpoint: Endpoint) -> None:
    """
    Helper function to gather all diagnostics for the current file and notify the client
    """
    publish_diagnostics_dict = {
        "uri": file_uri,
        "diagnostics": diagnostics,
    }

    endpoint.notify('textDocument/publishDiagnostics',publish_diagnostics_dict)

    return
