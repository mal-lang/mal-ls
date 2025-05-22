import argparse
import sys


def main():
    parser = argparse.ArgumentParser()
    configure_argument_parser(parser)
    parser.parse_args(sys.argv[1:])


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
        type=argparse.FileType("br"),
        help="Sets which (pseudo)file to use as input. Prioritized over --stdio.",
    )
    fileio.add_argument(
        "-o",
        "--out",
        type=argparse.FileType("bw"),
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


if __name__ == "__main__":
    main()
