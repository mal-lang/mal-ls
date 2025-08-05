import logging
import os
from pathlib import Path

import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser
from uritools import urisplit

from ..ts.utils import INCLUDED_FILES_QUERY, run_query
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


def recursive_parsing(uri_prec: str, captures: dict, storage: dict) -> None:
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
        root_node = tree.root_node

        # save parsed file
        storage[file_name] = Document(tree, source)

        # check if there are other includes to process
        new_captures = run_query(root_node, INCLUDED_FILES_QUERY)

        # if there are new includes, add them to the list
        if new_captures:
            captures.extend(new_captures["file_name"])

    return storage
