# General

## What is the MAL Language Server?

A Language Server is a backend service that provides advanced code editing features like
autocompletion, error checking, and refactoring to development tools (such as IDEs or editors).
This way, the server offers information about the code the programmer is editing, such as function
definition, parameters, etc.

The Meta Attack Language (MAL) is a programming language that allows cybersecurity analysts to model
their systems and find possible attack vectors, simplifying their tasks.

Therefore, the MAL Language Server aims to provide developers tools to more easily write and
comprehend MAL code.

## How does the MAL LS work?

In a language server scenario, there is a client (the IDE, editor, etc. that the developer is using)
and a server. They communicate via messages, which can be requests that include a response or
notifications - one way messages. The communication protocol is written in `JSON` and is standardized
according to the [Microsoft Documentation](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/). Since this is an RPC protocol (Remote Procedure Call), in many
cases the user "asks" the server to execute commands for them and return the appropriate results.
Hence, the user will ask the server to run functions related to the code the developer is working on
and the server will respond with the results - which in turn are more information about the code itself.

In short, the client and server exchange `JSON` messages to provide information about the code being
edited.
