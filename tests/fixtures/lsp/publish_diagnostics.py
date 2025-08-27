import typing

import pytest

# So that importers are aware of the conftest fixtures
pytest_plugins = [
    "tests.fixtures.lsp.conftest",
    "tests.fixtures.lsp.did_open_text_document_notification",
]


@pytest.fixture
def did_open_erroneous_notification(
    client_notifications: list[dict],
    did_open_notification,
    mal_erroneous: typing.BinaryIO,
    mal_erroneous_uri: str,
):
    # since did_open_notification is a dependency here
    # we know the notification is the latest one
    open_notification = client_notifications[-1]
    text_doc_params = open_notification["params"]["textDocument"]
    text_doc_params["uri"] = mal_erroneous_uri
    text_doc_params["text"] = mal_erroneous.read().decode("utf8")


@pytest.fixture
def erroneous_file_client_messages(
    initalize_request,
    initalized_notification,
    did_open_erroneous_notification,
    client_rpc_messages: typing.BinaryIO,
) -> typing.BinaryIO:
    return client_rpc_messages


@pytest.fixture
def did_open_erroneous_include_notification(
    client_notifications: list[dict],
    did_open_notification,
    mal_erroneous_include: typing.BinaryIO,
    mal_erroneous_include_uri: str,
):
    # since did_open_notification is a dependency here
    # we know the notification is the latest one
    open_notification = client_notifications[-1]
    text_doc_params = open_notification["params"]["textDocument"]
    text_doc_params["uri"] = mal_erroneous_include_uri
    text_doc_params["text"] = mal_erroneous_include.read().decode("utf8")


@pytest.fixture
def erroneous_include_file_client_messages(
    initalize_request,
    initalized_notification,
    did_open_erroneous_include_notification,
    client_rpc_messages: typing.BinaryIO,
) -> typing.BinaryIO:
    return client_rpc_messages


@pytest.fixture
def did_open_file_with_error_notification(
    client_notifications: list[dict],
    did_open_notification,
    mal_file_with_error: typing.BinaryIO,
    mal_file_with_error_uri: str,
):
    # since did_open_notification is a dependency here
    # we know the notification is the latest one
    open_notification = client_notifications[-1]
    text_doc_params = open_notification["params"]["textDocument"]
    text_doc_params["uri"] = mal_file_with_error_uri
    text_doc_params["text"] = mal_file_with_error.read().decode("utf8")


@pytest.fixture
def erroenous_include_and_file_with_error_client_messages(
    initalize_request,
    initalized_notification,
    did_open_erroneous_notification,
    did_open_file_with_error_notification,
    client_rpc_messages: typing.BinaryIO,
) -> typing.BinaryIO:
    return client_rpc_messages


@pytest.fixture
def did_change_with_error_notification(
    client_notifications: list[dict], did_change_notification, mal_base_open_uri: str
):
    client_notifications[-1]["params"] = {
        "textDocument": {
            "uri": mal_base_open_uri,
            "version": 1,
        },
        "contentChanges": [
            {
                "range": {
                    "start": {"line": 5, "character": 10},
                    "end": {"line": 6, "character": 0},
                },
                "text": "FooFoo extds Foo {}\n",
            }
        ],
    }


@pytest.fixture
def change_file_with_error_client_messages(
    initalize_request,
    initalized_notification,
    did_open_base_open_notification,
    did_change_with_error_notification,
    client_rpc_messages: typing.BinaryIO,
) -> typing.BinaryIO:
    return client_rpc_messages
