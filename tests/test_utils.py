"""
Test the test utils module
"""

from .util import fixture_name_from_file


def test_nominal_fixture_naming():
    path = "path/to/fixture.file"
    name = fixture_name_from_file(path)
    assert name == "path_to_fixture"


def test_fixture_naming_ignore_prefix():
    path = "path/to/fixture.file"
    name = fixture_name_from_file(path, root_folder="path/to")
    assert name == "fixture"


def test_fixture_naming_ignore_prefix_middle_of_path():
    path = "path/to/fixture.file"
    name = fixture_name_from_file(path, root_folder="to")
    assert name == "fixture"


def test_fixture_naming_rename_extension():
    path = "path/to/fixture.file"
    name = fixture_name_from_file(path, extension_renaming=lambda x: x)
    assert name == "path_to_fixture_file"


def test_fixture_naming_rename_extension_with_ignore_prefix():
    path = "path/to/fixture.file"
    name = fixture_name_from_file(path, extension_renaming=lambda x: x, root_folder="path/to")
    assert name == "fixture_file"
