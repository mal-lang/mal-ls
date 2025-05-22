import argparse
import logging
import pathlib
import sys

from . import __LOG_FORMAT__


def configure_argument_parser(parser: argparse.ArgumentParser, subparser: bool = False):
    """
    Configures the parser for usage with the MAL Language Server. If the parser is already used
    for other means (through `subparser` parameter), this simply adds a subparser.
    """
    if subparser:
        subparser = argparse.ArgumentParser("mal-ls", "MAL Language Server")
        parser.add_subparsers().add_parser(subparser)
        parser = subparser
    else:
        parser.description = "MAL Language Server"

    # File I/O
    fileio = parser.add_argument_group("File I/O", "Use the server through ")
    fileio.add_argument(
        "-i",
        "--in",
        dest="in_file_path",
        type=pathlib.Path,
        help="Sets which (pseudo)file to use as input. Prioritized over --stdio.",
    )
    fileio.add_argument(
        "-o",
        "--out",
        dest="out_file_path",
        type=pathlib.Path,
        help=("Sets which (pseudo)file to use as output. Prioritized over --stdio."),
    )
    fileio.add_argument(
        "--stdio",
        action="store_true",
        help=(
            "Use stdio for --in and --out. Use in conjunction with --in/out to customize"
            " only one of stdio."
        ),
    )

    # Loggin
    logging = parser.add_argument_group("Logging", "Configure logging options")
    logging.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increases the verbosity of the logging."
    )
    logging.add_argument("--log-file", type=argparse.FileType("w", encoding="utf8"))
    # logging.add_argument("--version", "-V", action="version", version="%(prog)s v" + __version__)

def uses_fileio(args: argparse.Namespace) -> bool:
   return bool(args.stdio or args.in_file_path or args.out_file_path)

def fileio(args: argparse.Namespace):
    in_file = open(args.in_file_path, "br") \
            if args.in_file_path \
            else sys.stdin.buffer
    out_file = open(args.out_file_path, "bw") \
            if args.out_file_path \
            else sys.stdout.buffer
    return in_file, out_file

def configure_logging(args: argparse.Namespace) -> None:
    root_logger = logging.root
    verbosity: int = args.verbose
    log_file: pathlib.Path = argparse.log_file

    formatter = logging.Formatter(__LOG_FORMAT__)
    if log_file:
        log_handler = logging.handlers.RotatingFileHandler(
                log_file,
                mode="a",
                maxBytes=50 * 1024 * 1024,
                backupCount=10,
                encoding="utf8",
                delay=0)
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

def main():
    parser = argparse.ArgumentParser()
    configure_argument_parser(parser)
    args = parser.parse_args()

    configure_logging(args)

    if uses_fileio(args):
        i, o = fileio(args)

if __name__ == "__main__":
    main()
