# Tests

The tests are split up into three sections; fixtures, integration tests, and unit tests. Fixtures
are then split further, into LSP fixtures and MAL fixtures.

## Integration tests

These tests are gennerally tests that take some kind of recorded or constructed LSP message stream,
input it into the server, and inspects the output or the state of the server.

Many of these tests are paratremized with fixture names and have the fixtures dynamically requested
since the underlying testing logic is the same (such as files or message streams). This also makes
it more maintainable and overall easier to understand, though it may be a bit more confusing
connecting the parameters and their purpose.

## Unit tests

Unit tests are dedicated to testing small units, therefore the name, and is no different here.
Things like individual algorithms and helper functions are tested here.

## LSP Fixtures

The LSP fixtures have a component system to them. Since the LSP is built on JSON RPC, most of these
fixtures are an individual JSON RPC message from client to server or vice versa. For example:

`tests/fixtures/lsp/conftest.py`
```py
@pytest.fixture
def initalize_request(client_requests: list[dict], client_messages: list[dict]) -> dict:
    """
    Defines an `initalize` LSP request from client to server.
    """
    message = {
        "jsonrpc": "2.0",
        "id": len(client_requests),
        "method": "initialize",
        "params": {
            "capabilities": {
                "textDocument": {
                    "definition": {"dynamicRegistration": False},
                    "synchronization": {"dynamicRegistration": False},
                }
            },
            "trace": "off",
        },
    }
    client_requests.append(message)
    client_messages.append(message)
    return message
```

The most common of these are available in the shared `conftest.py` of the LSP fixture folder.
However, sometimes these fixtures need to be specialized or edited, which can be done simply
(and by recommendation) by requesting the fixture and editing the last message:

`tests/fixtures/lsp/trace.py`
```py
@pytest.fixture
def set_trace_notification(client_notifications: list[dict], client_messages: list[dict]) -> dict:
    """
    Sends a $/setTrace notification from the client to the server.
    `value` must be set in params.
    """
    message = {"jsonrpc": "2.0", "method": "$/setTrace", "params": {}}
    client_notifications.append(message)
    client_messages.append(message)
    return message


@pytest.fixture
def set_trace_verbose_notification(client_notifications: list[dict], set_trace_notification):
    client_notifications[-1]["params"]["value"] = "verbose"
```

They are then built together by simply requesting the fixtures in order and the specialized
`client_rpc_messages` that builds them into an actual JSON RPC message stream:

`tests/fixtures/lsp/trace.py`
```py
@pytest.fixture
def set_trace_wrong_client_messages(
    client_initalize_procedures,
    set_trace_wrong_notification,
    client_shutdown_procedures,
    client_rpc_messages: typing.BinaryIO,
) -> typing.BinaryIO:
    return client_rpc_messages
```

## MAL Fixtures

The MAL files located in `tests/fixtures/mal/` are automatically loaded by the root `conftest.py`.
To request one of the, simply specifiy the file name without the extension and the prefix `mal_`.
For example, for a file `tests/fixtures/mal/hello_world.mal`, it can be requested as
`mal_hello_world`. The files are opened as read-only binary, so decoding will have to be done as
extra setup by tests/fixtures if necessary. These should never be changed to be writable since
fixture data should never be edited. If anything needs to be added, create a new fixture that
either creates a temporary file that it modifies and hands over or load the file into memory and
modify the memory.
