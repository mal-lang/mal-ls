import asyncio
import io
import json
import typing
from pathlib import Path

from pylsp_jsonrpc.endpoint import Endpoint
from pylsp_jsonrpc.exceptions import JsonRpcException
from pylsp_jsonrpc.streams import JsonRpcStreamReader

from malls.mal_lsp import MALLSPServer


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
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 12},
                },
                "text": {"text": '#id: "a.b.c"\n'},
            }
        ],
    },
}
