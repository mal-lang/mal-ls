import logging
import typing
from pathlib import Path
import json
from tree_sitter import Tree

from malls.lsp.enums import ErrorCodes, TraceValue

from ..util import get_lsp_json, server_output

log = logging.getLogger(__name__)

# calculate file path of mal files
FILE_PATH = str(Path(__file__).parent.parent.resolve())+"/fixtures/mal/"

def filepath_to_uri(filepath: str) -> str:
    """
    Converts a native filesystem path to a file:// URI.
    """
    path_obj = Path(filepath)

    absolute_path_obj = path_obj.resolve()

    return absolute_path_obj.as_uri()

def test_open_file_without_include(writeable_fixtures_did_open_notif_in: typing.BinaryIO):
    # go to start of file
    writeable_fixtures_did_open_notif_in.seek(0)
    # ignore first 4 lines (153 bytes)
    writeable_fixtures_did_open_notif_in.seek(153)

    # create fake uri for the MAL file being parsed 
    # (won't be used by the server, so there is no issue if the file does not actually exist)
    simplified_file_path = FILE_PATH + "main.mal"
    file_path = filepath_to_uri(simplified_file_path)

    # construct payload with correct uri
    payload = {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":file_path,"languageId":"mal","version":0,"text":"#id: \"org.mal-lang.testAnalyzer\"\n#version:\"0.0.0\"\n\ncategory System {\nabstract asset Foo {}\nasset Bar extends Foo {}\n}\n\n"}}}

    # get the length of the payload (+1 for the newline)
    json_string = json.dumps(payload, separators=(',', ':'))  # Remove extra spaces
    json_payload = json_string.encode('utf-8')
    payload_size = str(len(json_payload)+1)

    # write payload and size to file
    writeable_fixtures_did_open_notif_in.write(b"Content-Length: "+payload_size.encode())
    writeable_fixtures_did_open_notif_in.write(b"\n\n"+json_string.encode())

    # go back to start of file
    writeable_fixtures_did_open_notif_in.seek(0)

    # send to server
    output, ls, *_ = server_output(writeable_fixtures_did_open_notif_in)

    # delete added lines
    writeable_fixtures_did_open_notif_in.seek(0)
    writeable_fixtures_did_open_notif_in.truncate(153)

    # Ensure LSP stored everything correctly
    assert simplified_file_path in ls.files().keys()
    assert type(ls.files()[simplified_file_path]) == Tree

    output.close()

def test_open_file_with_include(writeable_fixtures_did_open_notif_in: typing.BinaryIO):
    # go to start of file
    writeable_fixtures_did_open_notif_in.seek(0)
    # ignore first 4 lines (153 bytes)
    writeable_fixtures_did_open_notif_in.seek(153)

    # create fake uri for the MAL file being parsed 
    # (won't be used by the server, so there is no issue if the file does not actually exist)
    simplified_file_path = FILE_PATH + "main.mal"
    # path for the included file
    included_path_file = FILE_PATH + "find_current_scope_function.mal"
    file_path = filepath_to_uri(simplified_file_path)

    # construct payload with correct uri
    payload = {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":file_path,"languageId":"mal","version":0,"text":"#id: \"org.mal-lang.testAnalyzer\"\n#version:\"0.0.0\"\ninclude \"find_current_scope_function.mal\"\ncategory System {\nabstract asset Foo {}\nasset Bar extends Foo {}\n}\n\n"}}}

    # get the length of the payload (+1 for the newline)
    json_string = json.dumps(payload, separators=(',', ':'))  # Remove extra spaces
    json_payload = json_string.encode('utf-8')
    payload_size = str(len(json_payload)+1)

    # write payload and size to file
    writeable_fixtures_did_open_notif_in.write(b"Content-Length: "+payload_size.encode())
    writeable_fixtures_did_open_notif_in.write(b"\n\n"+json_string.encode())

    # go back to start of file
    writeable_fixtures_did_open_notif_in.seek(0)

    # send to server
    output, ls, *_ = server_output(writeable_fixtures_did_open_notif_in)

    # delete added lines
    writeable_fixtures_did_open_notif_in.seek(0)
    writeable_fixtures_did_open_notif_in.truncate(153)

    # Ensure LSP stored everything correctly
    assert len(ls.files().keys())==2
    assert simplified_file_path in ls.files().keys()
    assert type(ls.files()[simplified_file_path]) == Tree
    assert included_path_file in ls.files().keys()
    assert type(ls.files()[included_path_file]) == Tree

    output.close()

def test_open_file_with_non_existant_include(writeable_fixtures_did_open_notif_in: typing.BinaryIO):
    # go to start of file
    writeable_fixtures_did_open_notif_in.seek(0)
    # ignore first 4 lines (153 bytes)
    writeable_fixtures_did_open_notif_in.seek(153)

    # create fake uri for the MAL file being parsed 
    # (won't be used by the server, so there is no issue if the file does not actually exist)
    simplified_file_path = FILE_PATH + "main.mal"
    # path for the included file
    included_path_file = FILE_PATH + "random_file_that_does_not_exist.mal"
    file_path = filepath_to_uri(simplified_file_path)

    # construct payload with correct uri
    payload = {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":file_path,"languageId":"mal","version":0,"text":"#id: \"org.mal-lang.testAnalyzer\"\n#version:\"0.0.0\"\ninclude \"random_file_that_does_not_exist.mal\"\ncategory System {\nabstract asset Foo {}\nasset Bar extends Foo {}\n}\n\n"}}}

    # get the length of the payload (+1 for the newline)
    json_string = json.dumps(payload, separators=(',', ':'))  # Remove extra spaces
    json_payload = json_string.encode('utf-8')
    payload_size = str(len(json_payload)+1)

    # write payload and size to file
    writeable_fixtures_did_open_notif_in.write(b"Content-Length: "+payload_size.encode())
    writeable_fixtures_did_open_notif_in.write(b"\n\n"+json_string.encode())

    # go back to start of file
    writeable_fixtures_did_open_notif_in.seek(0)

    # send to server
    output, ls, *_ = server_output(writeable_fixtures_did_open_notif_in)

    # delete added lines
    writeable_fixtures_did_open_notif_in.seek(0)
    writeable_fixtures_did_open_notif_in.truncate(153)

    # Ensure LSP stored everything correctly
    assert len(ls.files().keys())== 1
    assert simplified_file_path in ls.files().keys()
    assert type(ls.files()[simplified_file_path]) == Tree
    
    # Ensure there is an error on the response corresponding to invalid
    # parameter, since "traceValue" is wrong

    output.close()
