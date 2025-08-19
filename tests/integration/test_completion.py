import logging
from pathlib import Path

import pytest
import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser

from ..util import get_lsp_json, server_output

log = logging.getLogger(__name__)
MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)
FILE_PATH = str(Path(__file__).parent.parent.resolve()) + "/fixtures/mal/"

simplified_file_path = FILE_PATH + "main.mal"

symbols_in_category_hierarchy = [
    "Asset1",
    "Asset2",
    "Asset3",
    "extends",
    "abstract",
    "asset",
    "info",
]
symbols_in_associations_hierarchy = [
    "a",
    "c",
    "d",
    "e",
    "L",
    "M",
    "Asset1",
    "Asset2",
]
symbols_in_asset1_hierarchy = [
    "var",
    "c",
    "compromise",
    "destroy",
    "let",
    "info",
]
symbols_in_asset2_hierarchy = [
    "destroy",
    "let",
    "info",
]
symbols_in_root_node_hierarchy = [
    "info",
    "category",
    "associations",
]

parameters = [
    ("completion_category", symbols_in_category_hierarchy),
    ("completion_associations", symbols_in_associations_hierarchy),
    ("completion_asset1", symbols_in_asset1_hierarchy),
    ("completion_asset2", symbols_in_asset2_hierarchy),
    ("completion_root_node", symbols_in_root_node_hierarchy),
]


@pytest.mark.parametrize(
    "fixture_name,completion_list",
    [(fixture_name, completion_list) for fixture_name, completion_list in parameters],
)
def test_completion(request, fixture_name, completion_list):
    # send to server
    fixture = request.getfixturevalue(fixture_name)
    output, ls, *_ = server_output(fixture)

    output.seek(0)
    response = get_lsp_json(output)
    response = get_lsp_json(output)

    returned_completion_list = []
    for item in response["result"]:
        returned_completion_list.append(item["label"])

    assert set(returned_completion_list) == set(completion_list)

    output.close()
