import argparse
import logging
import pathlib
import socket
import sys

from . import __LOG_FORMAT__
from .mal_lsp import start_fileio_server


def configure_argument_parser(parser: argparse.ArgumentParser, subparser: bool = False):
    """
    Configures the parser for usage with the MAL Language Server. If the parser is already used
    for other means (through `subparser` parameter), this simply adds a subparser.

    Users must choose EITHER file I/O OR TCP socket mode (mutually exclusive).
    """
    description = """
                 MAL Language server.
                 By default uses STDI/O.
                 """
    if subparser:
        subparser = argparse.ArgumentParser(prog="mal-ls", description=description)
        parser.add_subparsers().add_parser(subparser)
        parser = subparser
    else:
        parser.description = description

    # ---- Mutually Exclusive Group: File I/O vs. TCP Socket ----
    mode_group = parser.add_mutually_exclusive_group()

    # File I/O
    file_group = mode_group.add_argument_group("File I/O", "Use file-based communication")
    file_group.add_argument(
        "-i",
        "--in",
        dest="in_file_path",
        type=pathlib.Path,
        help="Sets which (pseudo)file to use as input. Prioritized over --stdio.",
    )
    file_group.add_argument(
        "-o",
        "--out",
        dest="out_file_path",
        type=pathlib.Path,
        help=("Sets which (pseudo)file to use as output. Prioritized over --stdio."),
    )

    # TCP Socket Mode
    tcp_group = mode_group.add_argument_group("TCP Socket", "Use TCP socket communication")
    tcp_group.add_argument(
        "--host",
        type=str,
        default="localhost",
        dest="host",
        help="Host to bind the TCP server to (default: localhost).",
    )
    tcp_group.add_argument(
        "-p",
        "--port",
        type=int,
        default=8080,
        dest="port",
        help="Port to bind the TCP server to (default: 8080).",
    )

    mode_group.add_argument(
        "--stdio", action=argparse.BooleanOptionalAction, default=True, help="Use stdio"
    )
    mode_group.add_argument(
        "--tcp", action=argparse.BooleanOptionalAction, default=False, help="Use TCP mode"
    )

    # Loggin
    logging = parser.add_argument_group("Logging", "Configure logging options")
    logging.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=(
            "Increases the verbosity of the logging."
            " None (0)  = Warning |"
            " -v (1)  = Info |"
            " -vv (2+) = Debug"
        ),
    )
    logging.add_argument("--log-file", type=argparse.FileType("w", encoding="utf8"))
    # logging.add_argument("--version", "-V", action="version", version="%(prog)s v" + __version__)


def uses_fileio(args: argparse.Namespace) -> bool:
    return bool(args.stdio or args.in_file_path or args.out_file_path)


def fileio(args: argparse.Namespace):
    in_file = open(args.in_file_path, "rb") if args.in_file_path else sys.stdin.buffer
    out_file = open(args.out_file_path, "wb") if args.out_file_path else sys.stdout.buffer
    return in_file, out_file


def uses_tcpsocket(args: argparse.Namespace) -> bool:
    return args.tcp


def tcpsocket(args: argparse.Namespace):
    host = args.host if args.host else "localhost"
    port = args.port if args.port else 8080

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))

    # Listen for one incoming connection at a time
    server_socket.listen(1)

    # blocks until a client connects
    conn, addr = server_socket.accept()

    # get file-like objects from the socket
    # this allows your existing server to work with TCP sockets
    in_stream = conn.makefile("rb")
    out_stream = conn.makefile("wb")

    return in_stream, out_stream


def configure_logging(args: argparse.Namespace) -> None:
    root_logger = logging.root
    verbosity: int = args.verbose
    log_file: pathlib.Path = args.log_file

    formatter = logging.Formatter(__LOG_FORMAT__)
    if log_file:
        log_handler = logging.handlers.RotatingFileHandler(
            log_file, mode="a", maxBytes=50 * 1024 * 1024, backupCount=10, encoding="utf8", delay=0
        )
    else:
        log_handler = logging.StreamHandler()
    log_handler.setFormatter(formatter)
    root_logger.addHandler(log_handler)

    if verbosity == 0:
        level = logging.WARNING
    elif verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    root_logger.setLevel(level)


def main(args: argparse.Namespace | None = None):
    if not args:
        parser = argparse.ArgumentParser()
        configure_argument_parser(parser)
        args = parser.parse_args()

    configure_logging(args)

    # Default to STDI/O
    if uses_tcpsocket(args):
        i, o = tcpsocket(args)
        start_fileio_server(i, o)
    else:
        # In case a check is needed, use `uses_fileio(args)`
        i, o = fileio(args)
        start_fileio_server(i, o)


if __name__ == "__main__":
    main()
