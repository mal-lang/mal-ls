import asyncio
import glob
import io
import json
import os
import typing
from os import path
from pathlib import Path

import pytest
import uritools
from pylsp_jsonrpc.endpoint import Endpoint
from pylsp_jsonrpc.exceptions import JsonRpcException
from pylsp_jsonrpc.streams import JsonRpcStreamReader

from malls.mal_lsp import MALLSPServer


def find_last_request(
    requests: list[dict], condition: typing.Callable[[dict], bool] | str, default=None
) -> dict:
    """
    Searches through the list of requests in reverse order and returns first (logically last)
    element fulfilling the condition. If condition is a string, then it finds the last request
    with the method matching the string.

    If none are found an error is raised unless a default is provided, which is returned instead.
    """
    if isinstance(condition, str):
        method_name = condition

        def condition(request: dict) -> bool:
            request.get("method") == method_name

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
    if isinstance(file_name, Path):
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


def load_file_as_fixture(
    path: str | Path,
    extension_renaming: typing.Callable[[str], str] | dict[str, str] | None = None,
    root_folder: str | None = None,
) -> (typing.Callable, str, typing.Callable, str):
    """
    Load the raw contents of a file as a fixture and its name, accompanied by uri as fixture and
    its name.

    Shares options with `fixture_name_from_file`.
    """

    # Generate a function that handles openening/closing of the file for fixture purposes.
    def open_fixture_file(file: str):
        def template() -> typing.BinaryIO:
            """Opens a fixture in (r)ead (b)inary mode. See `open` for more details."""

            with open(file, "rb") as file_descriptor:
                yield file_descriptor

            return template

    def fixture_uri(file_path: str | Path):
        uri = uritools.uricompose(scheme="file", path=str(file_path))

        def template() -> str:
            return uri

    fixture_name = fixture_name_from_file(
        path, extension_renaming=extension_renaming, root_folder=root_folder
    )

    fixture = pytest.fixture(
        open_fixture_file(path),
        name=fixture_name,
    )

    uri_fixture_name = fixture_name + "_uri"

    uri_fixture = pytest.fixture(fixture_uri(Path(path).absolute()), name=uri_fixture_name)

    return fixture, fixture_name, uri_fixture, uri_fixture_name


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
    fixture, fixture_name, *_ = load_file_as_fixture(
        path, extension_renaming=extension_renaming, root_folder=root_folder
    )
    setattr(module, fixture_name, fixture)


def load_directory_files_as_fixtures(
    dir_path: str | Path,
    extension: str | None = None,
    extension_renaming: typing.Callable[[str], str] | dict[str, str] | None = None,
) -> [(typing.Callable, str, typing.Callable, str)]:
    """
    Loads all file contents in a given directory, aside from .py, and their URI's as fixtures,
    using `load_file_as_fixture`.

    Shares option `extension_renaming` with `fixture_name_from_file`.
    """
    if isinstance(dir_path, Path):
        dir_path = str(dir_path.absolute())
    # Find all files in the directory with the extension, or if none is provided
    # all non-python files
    if extension:
        # Glob find all files matching the extension in the given directory
        files = glob.iglob(path.join(dir_path, f"*.{extension}"))
    else:
        # Filter all entries in the directory to non-python files
        def non_python_file(entry: os.DirEntry) -> bool:
            return entry.is_file() and not entry.path.endswith(".py")

        file_entries = os.scandir(dir_path)
        non_python_file_entries = filter(non_python_file, file_entries)
        files = (entry.path for entry in non_python_file_entries)

    # Concat the file names with the directory to get relative to root path
    # then load the file as a fixture, getting the name and absolute path in the process
    file_paths = (path.join(dir_path, file) for file in files)
    fixture_name_paths = (load_file_as_fixture(path, root_folder=dir_path) for path in file_paths)
    return list(fixture_name_paths)


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
