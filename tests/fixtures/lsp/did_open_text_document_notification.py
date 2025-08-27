import typing

import pytest

# So that importers are aware of the conftest fixtures
pytest_plugins = ["tests.fixtures.lsp.conftest"]


@pytest.fixture
def did_open_base_open_notification(
    client_notifications: list[dict],
    client_messages: list[dict],
    did_open_notification,
    mal_base_open: typing.BinaryIO,
    mal_base_open_uri: str,
):
    # since did_open_notification is a dependency here
    # we know the notification is the latest one
    open_notification = client_notifications[-1]
    text_doc_params = open_notification["params"]["textDocument"]
    text_doc_params["uri"] = mal_base_open_uri
    text_doc_params["text"] = mal_base_open.read().decode("utf8")


@pytest.fixture
def base_open_client_messages(
    client_initalize_procedures,
    did_open_base_open_notification,
    client_rpc_messages: typing.BinaryIO,
) -> typing.BinaryIO:
    return client_rpc_messages


@pytest.fixture
def did_open_base_open_file_with_fake_include_notification(
    client_notifications: list[dict],
    client_messages: list[dict],
    did_open_notification,
    mal_base_open_file_with_fake_include: typing.BinaryIO,
    mal_base_open_file_with_fake_include_uri: str,
):
    # since did_open_notification is a dependency here
    # we know the notification is the latest one
    open_notification = client_notifications[-1]
    text_doc_params = open_notification["params"]["textDocument"]
    text_doc_params["uri"] = mal_base_open_file_with_fake_include_uri
    text_doc_params["text"] = mal_base_open_file_with_fake_include.read().decode("utf8")


@pytest.fixture
def base_open_file_with_fake_include_client_messages(
    client_initalize_procedures,
    did_open_base_open_file_with_fake_include_notification,
    client_rpc_messages: typing.BinaryIO,
) -> typing.BinaryIO:
    return client_rpc_messages


@pytest.fixture
def did_open_base_open_with_included_file_notification(
    client_notifications: list[dict],
    client_messages: list[dict],
    did_open_notification,
    mal_base_open_with_included_file: typing.BinaryIO,
    mal_base_open_with_included_file_uri: str,
):
    # since did_open_notification is a dependency here
    # we know the notification is the latest one
    open_notification = client_notifications[-1]
    text_doc_params = open_notification["params"]["textDocument"]
    text_doc_params["uri"] = mal_base_open_with_included_file_uri
    text_doc_params["text"] = mal_base_open_with_included_file.read().decode("utf8")


@pytest.fixture
def base_open_with_included_file_client_messages(
    client_initalize_procedures,
    did_open_base_open_with_included_file_notification,
    client_rpc_messages: typing.BinaryIO,
) -> typing.BinaryIO:
    return client_rpc_messages
