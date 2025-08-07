import logging
import typing
from pathlib import Path

from tree_sitter import Tree

from ..util import server_output

log = logging.getLogger(__name__)

# calculate file path of mal files
FILE_PATH = str(Path(__file__).parent.parent.resolve()) + "/fixtures/mal/"
simplified_file_path = FILE_PATH + "main.mal"


def filepath_to_uri(filepath: str) -> str:
    """
    Converts a native filesystem path to a file:// URI.
    """
    path_obj = Path(filepath)

    absolute_path_obj = path_obj.resolve()

    return absolute_path_obj.as_uri()


def test_open_file_without_include(
    writeable_fixtures_did_open_notif_in_base_open_file: typing.BinaryIO,
):
    # send to server
    output, ls, *_ = server_output(writeable_fixtures_did_open_notif_in_base_open_file)

    # Ensure LSP stored everything correctly
    assert simplified_file_path in ls.files.keys()
    assert type(ls.files[simplified_file_path].tree) is Tree

    output.close()


def test_open_file_with_include(
    writeable_fixtures_did_open_notif_in_with_included_file: typing.BinaryIO,
):
    # path for the included file
    included_path_file = FILE_PATH + "find_current_scope_function.mal"

    # send to server
    output, ls, *_ = server_output(writeable_fixtures_did_open_notif_in_with_included_file)

    # Ensure LSP stored everything correctly
    assert len(ls.files.keys()) == 2
    assert simplified_file_path in ls.files.keys()
    assert type(ls.files[simplified_file_path].tree) is Tree
    assert included_path_file in ls.files.keys()
    assert type(ls.files[included_path_file].tree) is Tree

    output.close()


def test_open_file_with_non_existant_include(
    writeable_fixtures_did_open_notif_in_with_fake_include: typing.BinaryIO,
):
    # send to server
    output, ls, *_ = server_output(writeable_fixtures_did_open_notif_in_with_fake_include)

    # Ensure LSP stored everything correctly
    assert len(ls.files.keys()) == 1
    assert simplified_file_path in ls.files.keys()
    assert type(ls.files[simplified_file_path].tree) is Tree

    output.close()
