import logging
import os
import sys
import typing
from pathlib import Path

import pytest
import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser

logging.getLogger().setLevel(logging.DEBUG)

module = sys.modules[__name__]
# Generate pytest fixtures from all fixture files in 'fixtures' and its subdirectories
for directory, _, files in os.walk("tests/fixtures"):
    if "__pycache__" in directory:
        continue
    for file_name in files:
        if file_name.endswith(".py") or file_name == "__pycache__":
            continue
        # Remove extension, e.g: .http/.lsp/.mal
        fixture_name = file_name[: file_name.rindex(".")]
        # Replace dots with underscore, e.g: empty.out -> empty_out
        fixture_name = fixture_name.replace(".", "_")
        # Add subdirectory path as prefix if there was one
        if len(directory) > len("tests/fixtures"):
            post_test_dir_index = directory.find("fixtures")
            # Remove up until tests plus directory delimiter
            fixture_prefix = directory[post_test_dir_index + len("fixtures") + 1 :]
            # Replace directory delimiters with underscores
            fixture_prefix = fixture_prefix.replace("/", "_").replace("\\", "_")
            fixture_name = fixture_prefix + "_" + fixture_name

        # Get full path of file so its usable by `open`
        file_path = os.path.join(directory, file_name)

        def open_fixture_file(file: str):
            def template() -> typing.BinaryIO:
                with open(file, "rb") as file_descriptor:
                    yield file_descriptor

            file_name = Path(file).name
            template.__doc__ = f"Opens {file_name} in (r)ead (b)inary mode and returns the reader."

            return template

        fixture = pytest.fixture(
            open_fixture_file(file_path),
            name=fixture_name,
        )
        # Bind `fixture` as `fixture_name` inside this module so it gets exported
        setattr(module, fixture_name, fixture)

        def fixture_uri(file: str):
            path = Path(file)
            file_path = path.resolve()
            uri = str(file_path.as_uri())

            def template() -> str:
                return uri

            file_name = path.name
            template.__doc__ = f"Returns the URI for {file_name} using file scheme."

            return template

        uri_fixture = pytest.fixture(
            fixture_uri(file_path),
            name=fixture_name + "_uri",
        )

        setattr(module, fixture_name + "_uri", uri_fixture)

TESTS_ROOT = Path(__file__).parent


@pytest.fixture
def tests_root() -> Path:
    return TESTS_ROOT


@pytest.fixture
def mal_root(tests_root: Path) -> Path:
    return tests_root.joinpath("fixtures", "mal")


@pytest.fixture
def mal_root_str(mal_root: Path) -> str:
    return str(mal_root)


@pytest.fixture
def mal_language() -> Language:
    return Language(ts_mal.language())


@pytest.fixture
def utf8_mal_parser(mal_language: Language) -> Parser:
    return Parser(mal_language)
