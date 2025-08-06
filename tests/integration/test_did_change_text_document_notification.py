import json
import logging
import typing
from pathlib import Path

import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser

from ..util import server_output

log = logging.getLogger(__name__)
MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)

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


def write_payload(payload, file):
    # get the length of the payload (+1 for the newline)
    json_string = json.dumps(payload, separators=(",", ":"))  # Remove extra spaces
    json_payload = json_string.encode("utf-8")
    payload_size = str(len(json_payload))

    # write payload and size to file
    file.write(b"Content-Length: " + payload_size.encode())
    file.write(b"\n\n" + json_string.encode())


def test_change_middle_of_file_single_line(change_middle_of_file_single_line: typing.BinaryIO):
    new_text = b"""#id: "org.mal-lang.testAnalyzer"
#version:"0.0.0"

category System {
abstract asset Foo {}
asset FooFoo extends Foo {}
}

"""
    # Start: 5 line | 13-7 = 6 character
    # End: 6 line | 0 character

    # send to server
    output, ls, *_ = server_output(change_middle_of_file_single_line)

    # Ensure LSP stored everything correctly
    assert ls.files[simplified_file_path].text == new_text
    # we have to parse the file to check if the end result is the same
    tree = PARSER.parse(new_text)
    assert str(ls.files[simplified_file_path].tree.root_node) == str(tree.root_node)

    output.close()


def test_change_middle_of_file_multiple_line(
    change_middle_of_file_multiple_lines: typing.BinaryIO,
):
    new_text = b"""#id: "org.mal-lang.testAnalyzer"
#version:"0.0.0"

category System {
abstract asset Bar {}
asset Foo extends Bar {}
}

"""
    # Start: 5 line | 13-7 = 6 character
    # End: 6 line | 0 character

    # send to server
    output, ls, *_ = server_output(change_middle_of_file_multiple_lines)

    # Ensure LSP stored everything correctly
    assert ls.files[simplified_file_path].text == new_text
    # we have to parse the file to check if the end result is the same
    tree = PARSER.parse(new_text)
    assert str(ls.files[simplified_file_path].tree.root_node) == str(tree.root_node)

    output.close()


def test_change_end_of_file(change_end_of_file: typing.BinaryIO):
    new_text = b"""#id: "org.mal-lang.testAnalyzer"
#version:"0.0.0"

category System {
abstract asset Foo {}
asset Bar extends Foo {}
}

associations {
}
"""
    # Start: 5 line | 13-7 = 6 character
    # End: 6 line | 0 character

    # send to server
    output, ls, *_ = server_output(change_end_of_file)

    # Ensure LSP stored everything correctly
    assert ls.files[simplified_file_path].text == new_text
    # we have to parse the file to check if the end result is the same
    tree = PARSER.parse(new_text)
    assert str(ls.files[simplified_file_path].tree.root_node) == str(tree.root_node)

    output.close()


def test_change_middle_of_file_twice(change_middle_of_file_twice: typing.BinaryIO):
    # construct change notificatoin payload with correct uri
    new_text = b"""#id: "org.mal-lang.testAnalyzer"
#version:"0.0.0"

category System {
abstract asset Bar {}
asset Qux extends Bar {}
}

"""
    # Start: 5 line | 13-7 = 6 character
    # End: 6 line | 0 character

    # send to server
    output, ls, *_ = server_output(change_middle_of_file_twice)

    # Ensure LSP stored everything correctly
    assert ls.files[simplified_file_path].text == new_text
    # we have to parse the file to check if the end result is the same
    tree = PARSER.parse(new_text)
    assert str(ls.files[simplified_file_path].tree.root_node) == str(tree.root_node)

    output.close()


def test_change_whole_file(change_whole_file: typing.BinaryIO):
    new_text = b"""#id: "a.b.c"\n"""
    # Start: 5 line | 13-7 = 6 character
    # End: 6 line | 0 character

    # send to server
    output, ls, *_ = server_output(change_whole_file)

    # Ensure LSP stored everything correctly
    assert ls.files[simplified_file_path].text == new_text
    # we have to parse the file to check if the end result is the same
    tree = PARSER.parse(new_text)
    assert str(ls.files[simplified_file_path].tree.root_node) == str(tree.root_node)

    output.close()
