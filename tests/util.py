import asyncio
import io
import json
import typing
from pathlib import Path

import pytest
from pylsp_jsonrpc.endpoint import Endpoint
from pylsp_jsonrpc.exceptions import JsonRpcException
from pylsp_jsonrpc.streams import JsonRpcStreamReader

from malls.mal_lsp import MALLSPServer


def find_last_request(requests: list[dict], condition: typing.Callable[[dict], bool], default=None):
    """
    Searches through the list of requests in reverse order and returns first (logically last)
    element fulfilling the condition.

    If none are found an error is raised unless a default is provided, which is returned instead.
    """
    return next(filter(condition, reversed(requests)), default)


def fixture_name_from_file(
    file_name: str | Path,
    extension_renaming: typing.Callable[[str], str] | dict[str, str] | None = None,
    root_folder: str | None = None,
) -> str:
    """
    Compute the name of a fixture based on its file path.

    Params:
        - `file_name`: A Path or str of the fixture.
        - `extension_renaming`: A function that takes in a string and outputs a string or
                                a dictionary mapping strings to strings, input will always
                                be the extension of the file. Default is to map to nothing.
        - `root_folder`: A root folder pattern. If supplied, anything up to and including
                         this value will be ignored when outputting the name. A following
                         slash will also be ignored.
    """
    # Default extension naming is none
    if extension_renaming is None:

        def extension_renaming(x: str):
            return ""

    # If a dictionary was provided, alias it as a function call to make it consistent with function
    # usage. If key/extension not present, default to no extension naming.
    if extension_renaming is dict:

        def extension_renaming(x: str):
            return extension_renaming.get(x, "")

    # Default to handling of strings
    if file_name is Path:
        file_name = str(file_name)

    # If a ignore prefix was given, find it and only care for anything after it
    # (on top of subsequent slash)
    if root_folder:
        post_prefix_index = file_name.find(root_folder)
        file_name = file_name[post_prefix_index + len(root_folder) + 1 :]

    extension_dot_index = file_name.rindex(".")
    extension = file_name[extension_dot_index + 1 :]
    # Remove extension, e.g: .http/.lsp/.mal
    fixture_name = file_name[:extension_dot_index]
    # Replace dots with underscore, e.g: empty.out -> empty_out
    fixture_name = fixture_name.replace(".", "_")
    # Add subdirectory path as prefix if there was one
    # Replace directory delimiters with underscores
    fixture_name = fixture_name.replace("/", "_").replace("\\", "_")
    # Add possible extension name
    if extension := extension_renaming(extension):
        fixture_name += "_" + extension

    return fixture_name


def load_fixture_file_into_module(
    path: str | Path,
    module,
    extension_renaming: typing.Callable[[str], str] | dict[str, str] | None = None,
    root_folder: str | None = None,
) -> None:
    """
    Load the raw contents of a file as a fixture into the provided module.

    Shares options with `fixture_name_from_file`.
    """

    # Generate a function that handles openening/closing of the file for fixture purposes.
    def open_fixture_file(file: str):
        def template() -> typing.BinaryIO:
            """Opens a fixture in (r)ead (b)inary mode. See `open` for more details."""

            with open(file, "rb") as file_descriptor:
                yield file_descriptor

            return template

    open_fixture_file.__doc__ = open.__doc__

    fixture_name = fixture_name_from_file(
        path, extension_renaming=extension_renaming, root_folder=root_folder
    )

    fixture = pytest.fixture(
        open_fixture_file(path),
        name=fixture_name,
    )
    # Bind `fixture` as `fixture_name` inside this module so it gets exported
    setattr(module, fixture_name, fixture)


CONTENT_TYPE_HEADER = b"Content-Type: application/vscode-jsonrpc; charset=utf8"


def build_rpc_message_stream(
    messages: list[dict],
    insert_header: typing.Callable[[dict, list[dict]], bytes | str] | bytes | str | None = None,
) -> io.BytesIO:
    buffer = io.BytesIO()
    for message in messages:
        # get the length of the payload (+1 for the newline)
        json_string = json.dumps(message, ensure_ascii=False, separators=(",", ":"))
        json_payload = json_string.encode("utf-8")
        payload_size = str(len(json_payload))

        # write payload size
        buffer.write(b"Content-Length: ")
        buffer.write(payload_size.encode())

        # Handle the setting of insert_header (fn, str, or bytes)
        if insert_header is not None:
            # Put header on new line
            buffer.write(b"\r\n")
            header = insert_header
            # If insert_header is a callback function, evaluate it for the current
            # message and total list of messages
            if callable(insert_header):
                header = insert_header(message, messages)
            # Encode strings into bytes
            if isinstance(insert_header, str):
                header = insert_header.encode("utf-8")
            # Insert header
            buffer.write(header)

        # Write header separator and payload
        buffer.write(b"\r\n\r\n")
        buffer.write(json_payload)
    buffer.seek(0)
    return buffer


def build_payload(to_include: list):
    result = b""
    for payload in to_include:
        # get the length of the payload (+1 for the newline)
        json_string = json.dumps(payload, separators=(",", ":"))  # Remove extra spaces
        json_payload = json_string.encode("utf-8")
        payload_size = str(len(json_payload))

        # write payload and size to file
        result += b"Content-Length: " + payload_size.encode() + b"\n\n" + json_string.encode()
    return result


def filepath_to_uri(filepath: str) -> str:
    """
    Converts a native filesystem path to a file:// URI.
    """
    path_obj = Path(filepath)

    absolute_path_obj = path_obj.resolve()

    return absolute_path_obj.as_uri()


def get_lsp_json(input_: io.BytesIO) -> tuple[dict, int]:
    # parse content length
    content_length = None
    while content_length is None:
        line = input_.readline()
        content_length = JsonRpcStreamReader._content_length(line)

    # find double newline
    while line != b"\r\n" and line != b"\n":
        line = input_.readline()

    # past double newline
    return json.loads(input_.read(content_length))


class FakeEndpoint(Endpoint):
    """
    Fake `Endpoint` to shadow, stub, and commandeer LSP `Endpoint` functions for testing.

    `request` is commandeered in order to make it execute sync but look async.
    """

    def request(self, method, params=None):
        request_future = super().request(method, params)
        try:
            request_future.set_result(self._dispatcher[method](params))
        except JsonRpcException as e:
            request_future.set_exception(e)

        return request_future

    request.__doc__ = Endpoint.request.__doc__


class FakeLanguageServer(MALLSPServer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("EndpointClass", FakeEndpoint)
        super().__init__(*args, **kwargs)


# wait for most 5s (arbitrary)
MAX_TIMEOUT = 2


class SteppedBytesIO(io.BytesIO):
    """
    SteppedBytesIO provide a way to stop the closing of the IO N-1 times, closing on the Nth time.
    """

    def __init__(self, initial_bytes: bytes = b"", steps: int = 1):
        self.steps = steps

    def close(self):
        if self.steps <= 0:
            super(io.BytesIO, self).close()
        else:
            self.steps -= 1


# TODO: create fake endpoint class (or similar) so the input can be stepped


# https://github.com/python-lsp/python-lsp-server/blob/develop/pylsp/python_lsp.py#L58
def server_output(
    input: typing.BinaryIO, timeout: float | None = MAX_TIMEOUT
) -> typing.Tuple[typing.BinaryIO, MALLSPServer, TimeoutError | None]:
    intermediary = SteppedBytesIO()
    ls = MALLSPServer(input, intermediary)
    time_out_err = None

    async def run_server():
        ls.start()

    try:
        server_future = run_server()
        asyncio.run(asyncio.wait_for(server_future, 1))
    except TimeoutError as e:
        ls.m_exit()
        time_out_err = e
    except Exception as e:
        intermediary.close()
        raise e

    return intermediary, ls, time_out_err


######################
# Pre-built payloads #
######################

# create fake uri for the MAL file being parsed
# (won't be used by the server, so there is no issue if the file does not actually exist)
FILE_PATH = str(Path(__file__).parent.resolve()) + "/fixtures/mal/"
main_simplified_file_path = FILE_PATH + "main.mal"
main_file_path = filepath_to_uri(main_simplified_file_path)
find_symbols_in_scope_path = filepath_to_uri(FILE_PATH + "find_symbols_in_scope.mal")

BASE_OPEN_FILE = {
    "jsonrpc": "2.0",
    "method": "textDocument/didOpen",
    "params": {
        "textDocument": {
            "uri": main_file_path,
            "languageId": "mal",
            "version": 0,
            "text": '#id: "org.mal-lang.testAnalyzer"\n#version:"0.0.0"\n\ncategory '
            + "System {\nabstract asset Foo {}\nasset Bar extends Foo {}\n}\n\n",
        }
    },
}

OPEN_FILE_WITH_INCLUDED_FILE = {
    "jsonrpc": "2.0",
    "method": "textDocument/didOpen",
    "params": {
        "textDocument": {
            "uri": main_file_path,
            "languageId": "mal",
            "version": 0,
            "text": '#id: "org.mal-lang.testAnalyzer"\n#version:"0.0.0"\
            \ninclude "find_current_scope_function.mal"\ncategory System\
            {\nabstract asset Foo {}\nasset Bar extends Foo {}\n}\n\n',
        }
    },
}

OPEN_FILE_WITH_FAKE_INCLUDE = {
    "jsonrpc": "2.0",
    "method": "textDocument/didOpen",
    "params": {
        "textDocument": {
            "uri": main_file_path,
            "languageId": "mal",
            "version": 0,
            "text": '#id: "org.mal-lang.testAnalyzer"\n#version:"0.0.0"\
            \ninclude "random_file_that_does_not_exist.mal"\ncategory System\
            {\nabstract asset Foo {}\nasset Bar extends Foo {}\n}\n\n',
        }
    },
}

CHANGE_FILE_1 = {
    "jsonrpc": "2.0",
    "method": "textDocument/didChange",
    "params": {
        "textDocument": {
            "uri": main_file_path,
            "version": 1,
        },
        "contentChanges": [
            {
                "range": {
                    "start": {"line": 5, "character": 6},
                    "end": {"line": 6, "character": 0},
                },
                "text": "FooFoo extends Foo {}\n",
            }
        ],
    },
}

CHANGE_FILE_2 = {
    "jsonrpc": "2.0",
    "method": "textDocument/didChange",
    "params": {
        "textDocument": {
            "uri": main_file_path,
            "version": 1,
        },
        "contentChanges": [
            {
                "range": {
                    "start": {"line": 4, "character": 15},
                    "end": {"line": 5, "character": 24},
                },
                "text": "Bar {}\nasset Foo extends Bar {}",
            }
        ],
    },
}

CHANGE_FILE_3 = {
    "jsonrpc": "2.0",
    "method": "textDocument/didChange",
    "params": {
        "textDocument": {
            "uri": main_file_path,
            "version": 1,
        },
        "contentChanges": [
            {
                "range": {
                    "start": {"line": 7, "character": 0},
                    "end": {"line": 9, "character": 0},
                },
                "text": "\nassociations {\n}\n",
            }
        ],
    },
}

CHANGE_FILE_4 = {
    "jsonrpc": "2.0",
    "method": "textDocument/didChange",
    "params": {
        "textDocument": {
            "uri": main_file_path,
            "version": 1,
        },
        "contentChanges": [
            {
                "range": {
                    "start": {"line": 4, "character": 15},
                    "end": {"line": 5, "character": 24},
                },
                "text": "Bar {}\nasset Foo extends Bar {}",
            },
            {
                "range": {
                    "start": {"line": 5, "character": 6},
                    "end": {"line": 5, "character": 9},
                },
                "text": "Qux",
            },
        ],
    },
}

CHANGE_FILE_5 = {
    "jsonrpc": "2.0",
    "method": "textDocument/didChange",
    "params": {
        "textDocument": {
            "uri": main_file_path,
            "version": 1,
        },
        "contentChanges": [
            {
                "text": '#id: "a.b.c"\n',
            }
        ],
    },
}


def build_goto_definition_payload(text: str, uri: str, line: int, char: int, name: str):
    open_message = {
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": main_file_path,
                "languageId": "mal",
                "version": 0,
                "text": text,
            }
        },
    }
    goto_message = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "textDocument/definition",
        "params": {
            "textDocument": {
                "uri": uri,
            },
            "position": {
                "line": line,
                "character": char,
            },
        },
    }
    return ([open_message, goto_message], name)


mal_find_symbols_in_scope_points = [
    (3, 12, "goto_def_1"),  # category_declaration
    (11, 10, "goto_def_2"),  # asset declaration, asset name
    (7, 10, "goto_def_3"),  # asset variable
    (8, 10, "goto_def_4"),  # attack step
]
mal_symbol_def_extended_asset_main_points = [
    (6, 25, "goto_def_5"),  # asset declaration, extended asset
    (9, 11, "goto_def_6"),  # variable call
]
mal_symbol_def_variable_call_extend_chain_main_points = [
    (9, 11, "goto_def_7")  # variable call, extend chain
]
symbol_def_variable_declaration_main_points = [
    (10, 20, "goto_def_8"),  # variable declaration
    (17, 21, "goto_def_9"),  # variable declaration, extended asset
    (21, 36, "goto_def_10"),  # variable declaration complex 1
    (22, 36, "goto_def_11"),  # variable declaration complex 2
    (26, 6, "goto_def_12"),  # association asset name 1
    (27, 37, "goto_def_13"),  # association asset name 2
    (28, 12, "goto_def_14"),  # association field name 1
    (28, 32, "goto_def_15"),  # association field name 2
    (30, 22, "goto_def_16"),  # link name
]
mal_symbol_def_preconditions_points = [
    (11, 15, "goto_def_17"),  # preconditions
    (19, 13, "goto_def_18"),  # preconditions extended asset
    (24, 28, "goto_def_19"),  # preconditions complex 1
    (26, 28, "goto_def_20"),  # preconditions complex 1
]
mal_symbol_def_reaches_points = [
    (13, 22, "goto_def_21"),  # reaches
    (14, 14, "goto_def_22"),  # reaches single attack step
    (10, 7, "goto_def_23"),  # random non-user defined symbol
]
GOTO_DEFINITION_PAYLOADS = (
    [
        build_goto_definition_payload(
            'include "find_symbols_in_scope.mal"', find_symbols_in_scope_path, line, char, name
        )
        for (line, char, name) in mal_find_symbols_in_scope_points
    ]
    + [
        build_goto_definition_payload(
            'include "symbol_def_extended_asset_main.mal"',
            filepath_to_uri(FILE_PATH + "symbol_def_extended_asset_main.mal"),
            line,
            char,
            name,
        )
        for (line, char, name) in mal_symbol_def_extended_asset_main_points
    ]
    + [
        build_goto_definition_payload(
            'include "symbol_def_variable_call_extend_chain_main.mal"',
            filepath_to_uri(FILE_PATH + "symbol_def_variable_call_extend_chain_main.mal"),
            line,
            char,
            name,
        )
        for (line, char, name) in mal_symbol_def_variable_call_extend_chain_main_points
    ]
    + [
        build_goto_definition_payload(
            'include "symbol_def_variable_declaration_main.mal"',
            filepath_to_uri(FILE_PATH + "symbol_def_variable_declaration_main.mal"),
            line,
            char,
            name,
        )
        for (line, char, name) in symbol_def_variable_declaration_main_points
    ]
    + [
        build_goto_definition_payload(
            'include "symbol_def_preconditions.mal"',
            filepath_to_uri(FILE_PATH + "symbol_def_preconditions.mal"),
            line,
            char,
            name,
        )
        for (line, char, name) in mal_symbol_def_preconditions_points
    ]
    + [
        build_goto_definition_payload(
            'include "symbol_def_reaches.mal"',
            filepath_to_uri(FILE_PATH + "symbol_def_reaches.mal"),
            line,
            char,
            name,
        )
        for (line, char, name) in mal_symbol_def_reaches_points
    ]
)

OPEN_FILE_WITH_ERROR = {
    "jsonrpc": "2.0",
    "method": "textDocument/didOpen",
    "params": {
        "textDocument": {
            "uri": main_file_path,
            "languageId": "mal",
            "version": 0,
            "text": '#id: "org.mal-lang.testAnalyzer"\n#version:"0.0.0"\n\ncategory '
            + "System {\nabstract aet Foo {}\nasset Bar extends Foo {}\n}\n\n",
        }
    },
}

OPEN_FILE_WITH_INCLUDE_WITH_ERROR = {
    "jsonrpc": "2.0",
    "method": "textDocument/didOpen",
    "params": {
        "textDocument": {
            "uri": main_file_path,
            "languageId": "mal",
            "version": 0,
            "text": '#id: "org.mal-lang.testAnalyzer"\n#version:"0.0.0"\
            \ninclude "file_with_error.mal"',
        }
    },
}

file_with_error_path = filepath_to_uri(FILE_PATH + "file_with_error.mal")
OPEN_INCLUDED_FILE_WITH_ERROR = {
    "jsonrpc": "2.0",
    "method": "textDocument/didOpen",
    "params": {
        "textDocument": {
            "uri": file_with_error_path,
            "languageId": "mal",
            "version": 0,
            "text": "class Category {\n    Asset1 {}\n  }\n",
        }
    },
}

CHANGE_FILE_WITH_ERROR = {
    "jsonrpc": "2.0",
    "method": "textDocument/didChange",
    "params": {
        "textDocument": {
            "uri": main_file_path,
            "version": 1,
        },
        "contentChanges": [
            {
                "range": {
                    "start": {"line": 5, "character": 6},
                    "end": {"line": 6, "character": 0},
                },
                "text": "FooFoo extds Foo {}\n",
            }
        ],
    },
}


def build_completion_payload(line, character, name):
    open = {
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": find_symbols_in_scope_path,
                "languageId": "mal",
                "version": 0,
                "text": """#id: "org.mal-lang.testAnalyzer"
#version:"0.0.0"

    category Example {

        abstract asset Asset1
        {
        let var = c
            | compromise
            -> var.destroy
        }
        asset Asset2 extends Asset3
        {
            | destroy
        }
    }
    associations
    {
        Asset1 [a] * <-- L --> * [c] Asset2
        Asset2 [d] 1 <-- M --> 1 [e] Asset2
    }
    """,
            }
        },
    }

    completion_list = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "textDocument/completion",
        "params": {
            "textDocument": {
                "uri": find_symbols_in_scope_path,
            },
            "position": {
                "line": line,
                "character": character,
            },
        },
    }

    return ([open, completion_list], name)


completion_items = [
    (4, 0, "completion_category"),
    (18, 0, "completion_associations"),
    (7, 0, "completion_asset1"),
    (13, 0, "completion_asset2"),
    (0, 0, "completion_root_node"),
]
COMPLETION_PAYLOADS = [
    build_completion_payload(line, char, name) for line, char, name in completion_items
]
