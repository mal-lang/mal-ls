import typing

import pytest

pytest_plugins = [
    "tests.fixtures.lsp.conftest",
    "tests.fixtures.lsp.did_open_text_document_notification",
]


@pytest.fixture
def did_change_base_open_notification(
    client_notifications: list[dict], mal_base_open_uri: str, did_change_notification
):
    client_notifications[-1]["params"] = {
        "textDocument": {
            "uri": mal_base_open_uri,
            "version": 1,
        },
    }


@pytest.fixture
def did_change_middle_of_base_open_single_line_notification(
    client_notifications: list[dict], did_change_base_open_notification
):
    client_notifications[-1]["params"]["contentChanges"] = [
        {
            "range": {
                "start": {"line": 5, "character": 10},
                "end": {"line": 6, "character": 0},
            },
            "text": "FooFoo extends Foo {}\n",
        }
    ]


@pytest.fixture
def change_middle_of_file_single_line_client_messages(
    client_initalize_procedures,
    did_open_base_open_notification,
    did_change_middle_of_base_open_single_line_notification,
    client_rpc_messages,
) -> typing.BinaryIO:
    return client_rpc_messages


@pytest.fixture
def did_change_middle_of_base_open_multiple_lines_notification(
    client_notifications: list[dict], did_change_base_open_notification
):
    client_notifications[-1]["params"]["contentChanges"] = [
        {
            "range": {
                "start": {"line": 4, "character": 19},
                "end": {"line": 5, "character": 28},
            },
            "text": "Bar {}\n    asset Foo extends Bar {}",
        }
    ]


@pytest.fixture
def change_middle_of_file_multiple_lines_client_messages(
    client_initalize_procedures,
    did_open_base_open_notification,
    did_change_middle_of_base_open_multiple_lines_notification,
    client_rpc_messages,
) -> typing.BinaryIO:
    return client_rpc_messages


@pytest.fixture
def did_change_end_of_base_open_notification(
    client_notifications: list[dict], did_change_base_open_notification
):
    client_notifications[-1]["params"]["contentChanges"] = [
        {
            "range": {
                "start": {"line": 7, "character": 0},
                "end": {"line": 9, "character": 0},
            },
            "text": "\nassociations {\n}\n",
        }
    ]


@pytest.fixture
def change_end_of_base_open_notification_client_messages(
    client_initalize_procedures,
    did_open_base_open_notification,
    did_change_end_of_base_open_notification,
    client_rpc_messages,
) -> typing.BinaryIO:
    return client_rpc_messages


@pytest.fixture
def did_change_middle_of_base_open_twice_notification(
    client_notifications: list[dict], did_change_base_open_notification
):
    client_notifications[-1]["params"]["contentChanges"] = [
        {
            "range": {
                "start": {"line": 4, "character": 19},
                "end": {"line": 5, "character": 28},
            },
            "text": "Bar {}\n    asset Foo extends Bar {}",
        },
        {
            "range": {
                "start": {"line": 5, "character": 10},
                "end": {"line": 5, "character": 13},
            },
            "text": "Qux",
        },
    ]


@pytest.fixture
def change_middle_of_base_open_twice_client_messages(
    client_initalize_procedures,
    did_open_base_open_notification,
    did_change_middle_of_base_open_twice_notification,
    client_rpc_messages,
) -> typing.BinaryIO:
    return client_rpc_messages


@pytest.fixture
def did_change_whole_base_open_notification(
    client_notifications: list[dict], did_change_base_open_notification
):
    client_notifications[-1]["params"]["contentChanges"] = [
        {
            "text": '#id: "a.b.c"\n',
        }
    ]


@pytest.fixture
def change_whole_base_open_client_messages(
    client_initalize_procedures,
    did_open_base_open_notification,
    did_change_whole_base_open_notification,
    client_rpc_messages,
) -> typing.BinaryIO:
    return client_rpc_messages
