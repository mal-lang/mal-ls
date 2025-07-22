import asyncio
import io
import logging
import typing

from malls.lsp.enums import ErrorCodes
from malls.lsp.fsm import LifecycleState
from malls.mal_lsp import MALLSPServer
import json

from pylsp_jsonrpc.streams import JsonRpcStreamReader

import urllib.parse
from pathlib import Path

def path_to_uri(file_path: str) -> str:
    """Convert local file path to file:// URI (works across OSes)"""
    absolute_path = Path(file_path).absolute()
    return urllib.parse.urlunparse((
        'file',
        '',  # Empty netloc
        str(absolute_path).replace('\\', '/'),  # Force forward slashes
        None, None, None
    ))


class SteppedBytesIO(io.BytesIO):
    """
    SteppedBytesIO provide a way to stop the closing of the IO N-1 times, closing on the Nth time.
    """
    def __init__(self, initial_bytes: bytes = b'', steps: int = 1):
        self.steps = steps

    def close(self):
        if self.steps <= 0:
            super(io.BytesIO, self).close()
        else:
            self.steps -= 1

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

def server_output(
        input: typing.BinaryIO,
        timeout: float | None = 10000) -> typing.Tuple[typing.BinaryIO, MALLSPServer, TimeoutError | None]:
    intermediary = SteppedBytesIO()
    ls = MALLSPServer(input, intermediary)
    
    async def run_server():
        ls.start()
    time_out_err = None

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

with open("tester.lsp","wb") as file: # start by writing the JSON_RPC message
    a = {"jsonrpc":"2.0","method":"example","params":{"textDocument":{"uri":path_to_uri("main.mal"),"text":"#id: \"org.mal-lang.testAnalyzer\"\n#version:\"0.0.0\"\ninclude \"aux.mal\"\n\ncategory System {\n    abstract asset Foo {}\n    asset Bar extends Foo {}\n}\n\n"}}}
    json_string = json.dumps(a, separators=(',', ':'))  # Remove extra spaces
    a = json_string.encode('utf-8')
    size = len(a)+1
    file.write(("Content Length: "+str(size)+"\n\n").encode('utf-8'))
    file.write(a)


file = open("test.lsp","rb")

output, ls, *_ = server_output(file)
