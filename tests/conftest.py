import logging
import os
import sys
import typing
from io import BytesIO

import pytest

from .util import (
    BASE_OPEN_FILE,
    OPEN_FILE_WITH_FAKE_INCLUDE,
    OPEN_FILE_WITH_INCLUDED_FILE,
    build_payload,
)

logging.getLogger().setLevel(logging.DEBUG)
log = logging.getLogger(__name__)

module = sys.modules[__name__]
# Generate pytest fixtures from all fixture files in 'fixtures' and its subdirectories
for directory, _, files in os.walk("tests/fixtures"):
    for file_name in files:
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

        def open_fixture_for_writing(file: str, payload: bytes):
            def template() -> typing.BinaryIO:
                with open(file, "rb") as file_descriptor:
                    bio = BytesIO(file_descriptor.read())

                bio.seek(0, 2)
                bio.write(payload)
                bio.seek(0)
                return bio

            return template

        def open_fixture_file(file: str):
            def template() -> typing.BinaryIO:
                """Opens a fixture in (r)ead (b)inary mode. See `open` for more details."""

                with open(file, "rb") as file_descriptor:
                    yield file_descriptor

            return template

        open_fixture_file.__doc__ = open.__doc__

        # Define the fixture from `open_file` on `file_path` as `fixture_name`
        if directory == "tests/fixtures/writeable_fixtures":
            # create different fixtures from the sabe base file
            payloads = [
                ([BASE_OPEN_FILE], fixture_name + "_base_open_file"),
                ([OPEN_FILE_WITH_INCLUDED_FILE], fixture_name + "_with_included_file"),
                ([OPEN_FILE_WITH_FAKE_INCLUDE], fixture_name + "_with_fake_include"),
            ]
            for payload, new_name in payloads:
                fixture = pytest.fixture(
                    open_fixture_for_writing(file_path, build_payload(payload)),
                    name=new_name,
                )
                # Bind `fixture` as `fixture_name` inside this module so it gets exported
                setattr(module, new_name, fixture)
        else:
            fixture = pytest.fixture(
                open_fixture_file(file_path),
                name=fixture_name,
            )
            # Bind `fixture` as `fixture_name` inside this module so it gets exported
            setattr(module, fixture_name, fixture)
