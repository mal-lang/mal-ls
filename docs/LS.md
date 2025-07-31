# Language Server

## Foundations

The MAL LS resorts to the [python JSON RPC server](https://github.com/python-lsp/python-lsp-jsonrpc) as
the foundation of the project. This package is a "bare-bones" implementation of a language server
written in Python, which can be extended to have a skeleton of the language server.

### [Streams](https://github.com/python-lsp/python-lsp-jsonrpc/blob/develop/pylsp_jsonrpc/streams.py)

Streams are the simplest component of the package and are simply used to receive and send messages to the
client. Very simply, streams will read the `JSON` message by using the `Content Length` header and give it
to the `Endpoint` to handle the message. Upon receiving a message to write, it will build that header and
send the received payload.

### [Endpoint](https://github.com/python-lsp/python-lsp-jsonrpc/blob/develop/pylsp_jsonrpc/endpoint.py)

Above all, this class facilitates communication, as it provides handlers for all types of incoming 
messages (requests and notifications) and allows the server to send messages to the client - responses
or otherwise. To do this, the Endpoint begins with `consume` which, as the name indicates, will receive
messages sent by the client. Afterwards, depending on the type of message, it will call the appropriate
method in the `Dispatcher`. Finally, the chosen method simply needs to return the appropriate response 
parameters, as this component will build the rest of the message and send the payload, by calling the
writing functionality of the `Streams`.

A relevant feature of the `Endpoint` is the ability to execute functions in parallel. In `_handle_request`,
the called function can return a callable, i.e. another function, which will be executed in parallel by
using threads.

### [Dispatcher](https://github.com/python-lsp/python-lsp-jsonrpc/blob/develop/pylsp_jsonrpc/dispatchers.py)

This component of the language server is *what* executes the commands requested by the user. In other
terms, the class `MethodDispatcher` is where the functions that the user requests are stored. The main
functionality this super class provides is the ability to find the name of the methods more easily and
in a standardized manner - starting with `m_`. Methods receive the parameters the client sent as arguments,
which can come in the form of a dictionary, if `**kwargs` is used, or named parameters.

## MAL LSP Server

The MAL LSP Server, represented in `mal_lsp.py`, is a subclass of the `MethodDispatcher`, i.e. where the
functions the user can request to run are stored. It contains an input and output buffer to communicate
with the client, which are handled by `Streams`. In return, when a message is received, the `Endpoint` will
ensure that the appropriate method is called. This can be found in the function `start`. As mentioned
above, all methods start with `m_`.

When the LSP Server receives requests from the clients, many of the requests require
capabilities which are not stored directly in the server class. To keep it as simple
as possible, the server should only be concerned with receiving and responding to
requests. Hence, the logic is stored in `ts/utils.py`. One of the most relevant details
is the position conversion. Clients send the positions of symbols they want to analyze
using UTF-XX encoding of the file's text, however TreeSitter works with byte-encoded
positions. Consequently, there is a helper function to convert from LSP positioning
to its TreeSitter counterpart. For now, the only supported encoding is UTF-16 which is
the default value. Furthermore, the server should be the one in charging of converting
positions before calling other additional methods, as these should work strictly with
TreeSitter positions.
