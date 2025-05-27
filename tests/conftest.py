import os
import sys
import typing

import pytest

module = sys.modules[__name__]
# Generate pytest fixtures from all fixture files in 'fixtures' and its subdirectories
for directory, _, files in os.walk("tests/fixtures"):
    for file_name in files:
        # Remove extension, e.g: .http/.lsp/.mal
        fixture_name = file_name[:file_name.rindex('.')]
        # Replace dots with underscore, e.g: empty.out -> empty_out
        fixture_name = fixture_name.replace(".", "_")
        # Add subdirectory path as prefix if there was one
        if len(directory) > len("tests/fixtures"):
            post_test_dir_index = directory.find("fixtures")
            # Remove up until tests plus directory delimiter
            fixture_prefix = directory[post_test_dir_index + len("fixtures") + 1:]
            # Replace directory delimiters with underscores
            fixture_prefix = fixture_prefix.replace("/", "_").replace("\\", "_")
            fixture_name = fixture_prefix + "_" + fixture_name

        # Get full path of file so its usable by `open`
        file_path = os.path.join(directory, file_name)

        def open_fixture_file() -> typing.BinaryIO:
            """Opens a fixture in (r)ead (b)inary mode. See `open` for more details."""
            with open(file_path, "rb") as file_descriptor:
                yield file_descriptor

        open_fixture_file.__doc__ = open.__doc__

        # Define the fixture from `open_file` on `file_path` as `fixture_name`
        fixture = pytest.fixture(
            fixture_function=open_fixture_file,
            name=fixture_name
        )

        # Bind `fixture` as `fixture_name` inside this module so it gets exported
        setattr(module, fixture_name, fixture)

