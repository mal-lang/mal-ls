import logging
import typing
from pylsp_jsonrpc.dispatchers import MethodDispatcher

log = logging.getLogger(__name__)
MAL_FILETYPES = (".mal",)


def start_fileio_server(in_file: typing.BinaryIO, out_file: typing.BinaryIO) -> None:
    log.info("Starting MAL LSP IO language server.")

class MALLSPServer(MethodDispatcher):
    pass
