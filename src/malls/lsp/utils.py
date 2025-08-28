import logging
import os
from pathlib import Path

import tree_sitter_mal as ts_mal
from pylsp_jsonrpc.endpoint import Endpoint
from tree_sitter import Language, Node, Parser
from uritools import urisplit

from ..ts.utils import (
    INCLUDED_FILES_QUERY,
    find_comments_function,
    find_meta_comment_function,
    find_symbols_in_current_scope,
    lsp_to_tree_sitter_position,
    query_for_error_nodes,
    run_query,
)
from .classes import Document
from .models import Position

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
        file_name = os.path.join(uri_prec, captures.pop(0).text.decode().strip('"'))

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
        "uri": path_to_uri(file_uri),
        "diagnostics": diagnostics,
    }

    endpoint.notify("textDocument/publishDiagnostics", publish_diagnostics_dict)

    return


def get_completion_list(doc: Document, pos: Position) -> list:
    # convert LSP position to TS point
    point = lsp_to_tree_sitter_position(doc.text, pos)

    # get completion items
    user_symbols, keywords = find_symbols_in_current_scope(doc.tree.walk(), point)

    # TODO include more relevant information
    # https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#completionItem

    completion_list = [{"label": symbol} for symbol in user_symbols.keys()] + [
        {"label": keyword} for keyword in keywords
    ]

    return completion_list


def build_markdown_meta_comments(meta_comments: list[Node]):
    markdown = ""
    for meta_comment in meta_comments:
        meta_id = meta_comment.child_by_field_name("id").text.decode()
        meta_info = meta_comment.child_by_field_name("info").text.decode()
        markdown += f"- **{meta_id}**: {meta_info}\n"
    return markdown


def sanitize_comment(comment: str):
    sanitized_comment = ""
    for line in comment:
        line = line.lstrip("/*")
        line = line.lstrip("*")
        line = line.lstrip("//")
        line = line.rstrip("*/")
        sanitized_comment += line if line != "\n" else ""
    return sanitized_comment


def build_markdown_comments(comments: list[Node]):
    markdown = ""
    for comment in comments:
        markdown += f"{sanitize_comment(comment.text.decode())}\n"
    return markdown


def get_hover_info(doc: Document, pos: Position, storage: dict) -> str:
    # convert LSP position to TS point
    point = lsp_to_tree_sitter_position(doc.text, pos)

    # get the symbol in that position
    cursor = doc.tree.walk()
    while cursor.goto_first_child_for_point(point) is not None:
        continue

    node = cursor.node
    if node.type != "identifier":
        return ""  # we can only find comments for identifiers

    # TODO write better hover info

    # get meta comments
    meta_title = "## **Meta comments**\n"
    meta_comments = find_meta_comment_function(node, node.text, doc.uri, storage)
    meta_markdown = build_markdown_meta_comments(meta_comments)

    # get regular comments
    comments_title = "## **Comments**\n"
    comments = find_comments_function(node, node.text, doc.uri, storage)
    comments_markdown = build_markdown_comments(comments)

    if meta_markdown and comments_markdown:
        return meta_title + meta_markdown + "---\n" + comments_title + comments_markdown

    return meta_title + meta_markdown if meta_markdown else comments_title + comments_markdown
