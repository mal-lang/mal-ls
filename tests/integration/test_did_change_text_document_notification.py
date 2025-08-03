import logging
import typing
from pathlib import Path
import json
from tree_sitter import Tree, Parser, Language
import tree_sitter_mal as ts_mal

from malls.lsp.enums import ErrorCodes, TraceValue

from ..util import get_lsp_json, server_output

log = logging.getLogger(__name__)
MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)

# calculate file path of mal files
FILE_PATH = str(Path(__file__).parent.parent.resolve())+"/fixtures/mal/"

def filepath_to_uri(filepath: str) -> str:
    """
    Converts a native filesystem path to a file:// URI.
    """
    path_obj = Path(filepath)

    absolute_path_obj = path_obj.resolve()

    return absolute_path_obj.as_uri()

def write_payload(payload, file):
    # get the length of the payload (+1 for the newline)
    json_string = json.dumps(payload, separators=(',', ':'))  # Remove extra spaces
    json_payload = json_string.encode('utf-8')
    payload_size = str(len(json_payload))

    # write payload and size to file
    file.write(b"Content-Length: "+payload_size.encode())
    file.write(b"\n\n"+json_string.encode())

def test_change_middle_of_file_single_line(writeable_fixtures_did_change_notif_in: typing.BinaryIO):
    # go to start of file
    writeable_fixtures_did_change_notif_in.seek(0)
    # ignore first 4 lines (153 bytes)
    writeable_fixtures_did_change_notif_in.seek(153)

    # create fake uri for the MAL file being parsed 
    # (won't be used by the server, so there is no issue if the file does not actually exist)
    simplified_file_path = FILE_PATH + "main.mal"
    file_path = filepath_to_uri(simplified_file_path)

    # construct payload with correct uri
    payload = {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":file_path,"languageId":"mal","version":0,"text":"#id: \"org.mal-lang.testAnalyzer\"\n#version:\"0.0.0\"\n\ncategory System {\nabstract asset Foo {}\nasset Bar extends Foo {}\n}\n\n"}}}
    write_payload(payload, writeable_fixtures_did_change_notif_in)

    # construct change notificatoin payload with correct uri
    payload = {"jsonrpc":"2.0","method":"textDocument/didChange","params":{"textDocument":{"uri":file_path,"version":1,},"contentChanges":[{"range":{"start":{"line":5,"character":6},"end":{"line":6,"character":0}},"text":"FooFoo extends Foo {}\n"}]}}
    write_payload(payload, writeable_fixtures_did_change_notif_in)

    new_text = b"""#id: "org.mal-lang.testAnalyzer"
#version:"0.0.0"

category System {
abstract asset Foo {}
asset FooFoo extends Foo {}
}

"""
    # Start: 5 line | 13-7 = 6 character
    # End: 6 line | 0 character

    # go back to start of file
    writeable_fixtures_did_change_notif_in.seek(0)

    # send to server
    output, ls, *_ = server_output(writeable_fixtures_did_change_notif_in)

    # delete added lines
    writeable_fixtures_did_change_notif_in.seek(0)
    writeable_fixtures_did_change_notif_in.truncate(153)

    # Ensure LSP stored everything correctly
    assert ls.files[simplified_file_path].text == new_text
    # we have to parse the file to check if the end result is the same
    tree = PARSER.parse(new_text)
    assert str(ls.files[simplified_file_path].tree.root_node) == str(tree.root_node)

    output.close()

def test_change_middle_of_file_multiple_line(writeable_fixtures_did_change_notif_in: typing.BinaryIO):
    # go to start of file
    writeable_fixtures_did_change_notif_in.seek(0)
    # ignore first 4 lines (153 bytes)
    writeable_fixtures_did_change_notif_in.seek(153)

    # create fake uri for the MAL file being parsed 
    # (won't be used by the server, so there is no issue if the file does not actually exist)
    simplified_file_path = FILE_PATH + "main.mal"
    file_path = filepath_to_uri(simplified_file_path)

    # construct payload with correct uri
    payload = {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":file_path,"languageId":"mal","version":0,"text":"#id: \"org.mal-lang.testAnalyzer\"\n#version:\"0.0.0\"\n\ncategory System {\nabstract asset Foo {}\nasset Bar extends Foo {}\n}\n\n"}}}
    write_payload(payload, writeable_fixtures_did_change_notif_in)

    # construct change notificatoin payload with correct uri
    payload = {"jsonrpc":"2.0","method":"textDocument/didChange","params":{"textDocument":{"uri":file_path,"version":1,},"contentChanges":[{"range":{"start":{"line":4,"character":15},"end":{"line":5,"character":24}},"text":"Bar {}\nasset Foo extends Bar {}"}]}}
    write_payload(payload, writeable_fixtures_did_change_notif_in)

    new_text = b"""#id: "org.mal-lang.testAnalyzer"
#version:"0.0.0"

category System {
abstract asset Bar {}
asset Foo extends Bar {}
}

"""
    # Start: 5 line | 13-7 = 6 character
    # End: 6 line | 0 character

    # go back to start of file
    writeable_fixtures_did_change_notif_in.seek(0)

    # send to server
    output, ls, *_ = server_output(writeable_fixtures_did_change_notif_in)

    # delete added lines
    writeable_fixtures_did_change_notif_in.seek(0)
    writeable_fixtures_did_change_notif_in.truncate(153)

    # Ensure LSP stored everything correctly
    assert ls.files[simplified_file_path].text == new_text
    # we have to parse the file to check if the end result is the same
    tree = PARSER.parse(new_text)
    assert str(ls.files[simplified_file_path].tree.root_node) == str(tree.root_node)

    output.close()

def test_change_end_of_file(writeable_fixtures_did_change_notif_in: typing.BinaryIO):
    # go to start of file
    writeable_fixtures_did_change_notif_in.seek(0)
    # ignore first 4 lines (153 bytes)
    writeable_fixtures_did_change_notif_in.seek(153)

    # create fake uri for the MAL file being parsed 
    # (won't be used by the server, so there is no issue if the file does not actually exist)
    simplified_file_path = FILE_PATH + "main.mal"
    file_path = filepath_to_uri(simplified_file_path)

    # construct payload with correct uri
    payload = {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":file_path,"languageId":"mal","version":0,"text":"#id: \"org.mal-lang.testAnalyzer\"\n#version:\"0.0.0\"\n\ncategory System {\nabstract asset Foo {}\nasset Bar extends Foo {}\n}\n\n"}}}
    write_payload(payload, writeable_fixtures_did_change_notif_in)

    # construct change notificatoin payload with correct uri
    payload = {"jsonrpc":"2.0","method":"textDocument/didChange","params":{"textDocument":{"uri":file_path,"version":1,},"contentChanges":[{"range":{"start":{"line":7,"character":0},"end":{"line":9,"character":0}},"text":"\nassociations {\n}\n"}]}}
    write_payload(payload, writeable_fixtures_did_change_notif_in)

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

    # go back to start of file
    writeable_fixtures_did_change_notif_in.seek(0)

    # send to server
    output, ls, *_ = server_output(writeable_fixtures_did_change_notif_in)

    # delete added lines
    writeable_fixtures_did_change_notif_in.seek(0)
    writeable_fixtures_did_change_notif_in.truncate(153)

    # Ensure LSP stored everything correctly
    assert ls.files[simplified_file_path].text == new_text
    # we have to parse the file to check if the end result is the same
    tree = PARSER.parse(new_text)
    assert str(ls.files[simplified_file_path].tree.root_node) == str(tree.root_node)

    output.close()

def test_change_middle_of_file_twice(writeable_fixtures_did_change_notif_in: typing.BinaryIO):
    # go to start of file
    writeable_fixtures_did_change_notif_in.seek(0)
    # ignore first 4 lines (153 bytes)
    writeable_fixtures_did_change_notif_in.seek(153)

    # create fake uri for the MAL file being parsed 
    # (won't be used by the server, so there is no issue if the file does not actually exist)
    simplified_file_path = FILE_PATH + "main.mal"
    file_path = filepath_to_uri(simplified_file_path)

    # construct payload with correct uri
    payload = {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":file_path,"languageId":"mal","version":0,"text":"#id: \"org.mal-lang.testAnalyzer\"\n#version:\"0.0.0\"\n\ncategory System {\nabstract asset Foo {}\nasset Bar extends Foo {}\n}\n\n"}}}
    write_payload(payload, writeable_fixtures_did_change_notif_in)

    # construct change notificatoin payload with correct uri
    payload = {"jsonrpc":"2.0","method":"textDocument/didChange","params":{"textDocument":{"uri":file_path,"version":1,},"contentChanges":[{"range":{"start":{"line":4,"character":15},"end":{"line":5,"character":24}},"text":"Bar {}\nasset Foo extends Bar {}"},{"range":{"start":{"line":5,"character":6},"end":{"line":5,"character":9}},"text":"Qux"}]}}
    write_payload(payload, writeable_fixtures_did_change_notif_in)

    new_text = b"""#id: "org.mal-lang.testAnalyzer"
#version:"0.0.0"

category System {
abstract asset Bar {}
asset Qux extends Bar {}
}

"""
    # Start: 5 line | 13-7 = 6 character
    # End: 6 line | 0 character

    # go back to start of file
    writeable_fixtures_did_change_notif_in.seek(0)

    # send to server
    output, ls, *_ = server_output(writeable_fixtures_did_change_notif_in)

    # delete added lines
    writeable_fixtures_did_change_notif_in.seek(0)
    writeable_fixtures_did_change_notif_in.truncate(153)

    # Ensure LSP stored everything correctly
    assert ls.files[simplified_file_path].text == new_text
    # we have to parse the file to check if the end result is the same
    tree = PARSER.parse(new_text)
    assert str(ls.files[simplified_file_path].tree.root_node) == str(tree.root_node)

    output.close()

def test_change_whole_file(writeable_fixtures_did_change_notif_in: typing.BinaryIO):
    # go to start of file
    writeable_fixtures_did_change_notif_in.seek(0)
    # ignore first 4 lines (153 bytes)
    writeable_fixtures_did_change_notif_in.seek(153)

    # create fake uri for the MAL file being parsed 
    # (won't be used by the server, so there is no issue if the file does not actually exist)
    simplified_file_path = FILE_PATH + "main.mal"
    file_path = filepath_to_uri(simplified_file_path)

    # construct payload with correct uri
    payload = {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":file_path,"languageId":"mal","version":0,"text":"#id: \"org.mal-lang.testAnalyzer\"\n#version:\"0.0.0\"\n\ncategory System {\nabstract asset Foo {}\nasset Bar extends Foo {}\n}\n\n"}}}
    write_payload(payload, writeable_fixtures_did_change_notif_in)

    # construct change notificatoin payload with correct uri
    payload = {"jsonrpc":"2.0","method":"textDocument/didChange","params":{"textDocument":{"uri":file_path,"version":1,},"contentChanges":[{"range":{"start":{"line":0,"character":0},"end":{"line":0,"character":12}},"text":{"text":"#id: \"a.b.c\"\n"}}]}}
    write_payload(payload, writeable_fixtures_did_change_notif_in)

    new_text = b"""#id: "a.b.c"\n"""
    # Start: 5 line | 13-7 = 6 character
    # End: 6 line | 0 character

    # go back to start of file
    writeable_fixtures_did_change_notif_in.seek(0)

    # send to server
    output, ls, *_ = server_output(writeable_fixtures_did_change_notif_in)

    # delete added lines
    writeable_fixtures_did_change_notif_in.seek(0)
    writeable_fixtures_did_change_notif_in.truncate(153)

    # Ensure LSP stored everything correctly
    assert ls.files[simplified_file_path].text == new_text
    # we have to parse the file to check if the end result is the same
    tree = PARSER.parse(new_text)
    assert str(ls.files[simplified_file_path].tree.root_node) == str(tree.root_node)

    output.close()
