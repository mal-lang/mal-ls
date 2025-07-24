# Contributing

## How to contribute

Besides reading this documentation, it is important to guarantee that all written code is compliant with
the workings of the python LSP RPC server package, as this is the back-bone of the project. Furthermore,
to make the LSP work with clients, all messages must follow the standards in the [Microsoft Documentation](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/). If this is not respected, it is possible that the client and server are not able to communicate
correctly, rendering the language server useless.

## Testing

It is important to include tests to ensure that new features work and that previous code do not start
malfunctioning. The tests often need parameters to run, such as the files used to communicate with the
server. To do this, simply add the test file to the `fixtures` folder (optionally inside a subfolder) and
they will be accessible as parameters by using the file name until the first `.`. For instance, the file
`log_trace_messages.in.lsp` can be accessed as a parameter with the name `log_trace_messages`.

Tests are implemented and ran using `pytest`. They can be run using `uv run pytest`. Optional arguments
are `-k TEST_NAME` to run a specific test or `-s` to include output.

