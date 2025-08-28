import io
import typing

import pytest

from ..util import build_rpc_message_stream, get_lsp_json, server_output

parameters = [
    (6, 11),
    (13, 20),
    (19, 15),
    (25, 12),
    (33, 7),
    (41, 13),
    (46, 13),
    (56, 13),
    (61, 13),
    (71, 21),
    (73, 21),
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


@pytest.mark.parametrize(
    "location,markdown_file", zip(parameters, parameter_names), ids=parameter_names
)
def test_hover(
    request: pytest.FixtureRequest,
    location: (int, int),
    markdown_file: str,
    hover_client_messages: typing.Callable[[(int, int)], io.BytesIO],
):
    file_fixture: typing.BinaryIO = request.getfixturevalue(f"markdown_{markdown_file}")
    # send to server
    fixture = hover_client_messages(location)
    output, *_ = server_output(fixture)

    output.seek(0)
    response = get_lsp_json(output)
    response = get_lsp_json(output)

    assert file_fixture.read().decode() == response["result"]["contents"]["value"]

    output.close()
