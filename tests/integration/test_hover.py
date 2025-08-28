import io
import typing

import pytest

from ..util import build_rpc_message_stream, get_lsp_json, server_output

pytest_plugins = ["tests.fixtures.lsp.conftest"]

comments_in_category = {
    "comments": ["// category comment"],
    "meta": {
        "developer": '"dev cat"',
        "modeler": '"mod cat"',
    },
}
comments_in_asset_1 = {
    "comments": ["// asset1 comment"],
    "meta": {"developer": '"dev asset"', "modeler": '"mod asset"'},
}
comments_in_attack_step1 = {
    "comments": ["// attack_step comment"],
    "meta": {"developer": '"dev attack_step"', "modeler": '"mod attack_step"'},
}
comments_in_attack_step2 = {"comments": ["// attack_step comment2"], "meta": {}}
comments_in_asset_3 = {
    "comments": ["// asset3 comment"],
    "meta": {"developer": '"dev asset3"', "modeler": '"mod asset3"'},
}
comments_in_asset_2 = {"comments": ["// asset2 comment"], "meta": {}}
comments_in_asset_4 = {
    "comments": [],
    "meta": {"developer": '"dev asset4"', "modeler": '"mod asset4"'},
}
comments_in_asset_5 = {
    "comments": [
        """/*
     * MULTI-LINE
     */"""
    ],
    "meta": {"developer": '"dev asset5"', "modeler": '"mod asset5"'},
}
comments_in_attack_step3 = {
    "comments": ["// attack_step comment3"],
    "meta": {"developer": '"dev attack_step_5"', "modeler": '"mod attack_step_5"'},
}
comments_in_association = {
    "comments": ["// association1 comment"],
    "meta": {
        "developer": '"some info"',
    },
}
comments_in_association2 = {"comments": ["// association2 comment"], "meta": {}}

parameters = [
    ((6, 11), comments_in_category),
    ((13, 20), comments_in_asset_1),
    ((19, 15), comments_in_attack_step1),
    ((25, 12), comments_in_attack_step2),
    ((33, 7), comments_in_asset_3),
    ((41, 13), comments_in_asset_2),
    ((46, 13), comments_in_asset_4),
    ((56, 13), comments_in_asset_5),
    ((61, 13), comments_in_attack_step3),
    ((71, 21), comments_in_association),
    ((73, 21), comments_in_association2),
]

parameter_names = [
    "comments_in_category",
    "comments_in_asset_1",
    "comments_in_attack_step1",
    "comments_in_attack_step2",
    "comments_in_asset_3",
    "comments_in_asset_2",
    "comments_in_asset_4",
    "comments_in_asset_5",
    "comments_in_attack_step3",
    "comments_in_association",
    "comments_in_association2",
]

pytest_plugins = ["tests.fixtures.mal"]


def sanitize_comment(comment: str):
    sanitized_comment = ""
    for line in comment:
        line = line.lstrip("/*")
        line = line.lstrip("*")
        line = line.lstrip("//")
        line = line.rstrip("*/")
        sanitized_comment += line if line != "\n" else ""
    return sanitized_comment


def build_comment(comments: dict):
    markdown = "\n# Symbol Info\n"
    markdown += "## **Meta comments**\n"
    for meta_id, meta_info in comments["meta"].items():
        markdown += f"- **{meta_id}**: {meta_info}\n"
    markdown += "---\n"
    markdown += "## **Comments**\n"
    for comment in comments["comments"]:
        markdown += f"- {sanitize_comment(comment)}\n"
    return markdown


@pytest.fixture
def open_hover_document_notification(
    client_notifications: list[dict],
    client_messages: list[dict],
    mal_hover_document: io.BytesIO,
    mal_hover_document_uri: str,
) -> dict:
    """
    Sends a didOpen notification bound to the MAL fixture file hover_document.
    """
    message = {
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": mal_hover_document_uri,
                "languageId": "mal",
                "version": 0,
                "text": mal_hover_document.read().decode("utf8"),
            }
        },
    }
    client_notifications.append(message)
    client_messages.append(message)
    return message


@pytest.fixture
def hover_request(
    client_requests: list[dict], client_messages: list[dict], mal_hover_document_uri: str
) -> typing.Callable[[(int, int)], dict]:
    def make(position: (int, int)):
        line, character = position
        message = {
            "id": len(client_requests),
            "jsonrpc": "2.0",
            "method": "textDocument/hover",
            "params": {
                "textDocument": {
                    "uri": mal_hover_document_uri,
                },
                "position": {
                    "line": line,
                    "character": character,
                },
            },
        }
        client_requests.append(message)
        client_messages.append(message)
        return message

    return make


@pytest.fixture
def hover_client_messages(
    client_messages: list[dict],
    initalize_request,
    initalized_notification,
    open_hover_document_notification,
    hover_request: typing.Callable[[(int, int)], dict],
) -> typing.Callable[[(int, int)], io.BytesIO]:  # noqa: E501
    def make(position: (int, int)) -> io.BytesIO:
        hover_request(position)
        return build_rpc_message_stream(client_messages)

    return make


@pytest.mark.parametrize("location,comments", parameters, ids=parameter_names)
def test_hover(
    location: (int, int),
    comments: dict,
    hover_client_messages: typing.Callable[[(int, int)], io.BytesIO],
):
    # send to server
    fixture = hover_client_messages(location)
    output, *_ = server_output(fixture)

    output.seek(0)
    response = get_lsp_json(output)
    response = get_lsp_json(output)

    assert build_comment(comments) == response["result"]["contents"]["value"]

    output.close()
