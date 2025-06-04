import io
import json

from pylsp_jsonrpc.streams import JsonRpcStreamReader


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
