import logging
from pathlib import Path
import typing

import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser

from malls.lsp.classes import Document
from malls.lsp.utils import recursive_parsing
from malls.ts.utils import INCLUDED_FILES_QUERY, find_symbol_definition, run_query
from ..util import server_output, get_lsp_json

log = logging.getLogger(__name__)
MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)
FILE_PATH = str(Path(__file__).parent.parent.resolve()) + "/fixtures/mal/"

simplified_file_path = FILE_PATH + "main.mal"


def filepath_to_uri(filepath: str) -> str:
    """
    Converts a native filesystem path to a file:// URI.
    """
    path_obj = Path(filepath)

    absolute_path_obj = path_obj.resolve()

    return absolute_path_obj.as_uri()


def test_goto_definition_category_declaration(
    find_symbol_1: typing.BinaryIO,
):
    # send to server
    output, ls, *_ = server_output(find_symbol_1)

    output.seek(0)
    response = get_lsp_json(output)
    response = get_lsp_json(output)


    start_point_dict = response["result"]["range"]["start"]
    start_point = (start_point_dict["line"], start_point_dict["character"])
    file = response["result"]["uri"]

    assert start_point == (3,0)
    assert file == filepath_to_uri(FILE_PATH+"find_symbols_in_scope.mal")

    output.close()
