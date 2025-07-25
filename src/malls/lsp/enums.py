"""LSP RPC enums

https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#basicJsonStructures
https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#lifeCycleMessages
https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_synchronization
"""

from enum import IntEnum, IntFlag, StrEnum


class EndOfLine(StrEnum):
    """
    To ensure that both client and server split the string into the same line representation the
    protocol specifies the following end-of-line sequences: '\\n', `\\r\\n` and `\r`. Positions are
    line end character agnostic. So you can not specify a position that denotes `\\r|\\n` or `\\n|`
    where `|` represents the character offset.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocuments
    """

    NL = "\n"
    CRNL = "\r\n"
    CR = "\r"


class PositionEncodingKind(StrEnum):
    """
    A set of predefined position encoding kinds indicating how positions are encoded, specifically
    what column offsets mean.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#positionEncodingKind
    """

    UTF8 = "utf-8"
    """Character offsets count UTF-8 code units (e.g bytes)."""

    UTF16 = "utf-16"
    """
    Character offsets count UTF-16 code units.

	This is the default and must always be supported by servers.
    """

    UTF32 = "utf-32"
    """
    Character offsets count UTF-32 code units.

	Implementation note: these are the same as Unicode code points, so this `PositionEncodingKind`
    may also be used for an encoding-agnostic representation of character offsets.
    """


class CompletionItemKind(IntEnum):
    """
    The kind of a completion entry.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#completionItemKind
    """

    Text = 1
    Method = 2
    Function = 3
    Constructor = 4
    Field = 5
    Variable = 6
    Class = 7
    Interface = 8
    Module = 9
    Property = 10
    Unit = 11
    Value = 12
    Enum = 13
    Keyword = 14
    Snippet = 15
    Color = 16
    File = 17
    Reference = 18
    Folder = 19
    EnumMember = 20
    Constant = 21
    Struct = 22
    Event = 23
    Operator = 24
    TypeParameter = 25


class CompletionItemTag(IntEnum):
    """
    Completion item tags are extra annotations that tweak the rendering of a
    completion item.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#completionItemTag
    """

    Deprecated = 1
    """Render a completion as obsolete, usually using a strike-out."""


class DiagnosticSeverity(IntEnum):
    """
    The severity of a diagnostic message.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#diagnosticSeverity
    """

    Error = 1
    """Reports an error."""

    Warning = 2
    """Reports a warning."""

    Information = 3
    """Reports information."""

    Hint = 4
    """Reports a hint."""


class DiagnosticTag(IntEnum):
    """
    The diagnostic tags.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#diagnosticTag
    """

    Unnecessary = 1
    """
    Unused or unnecessary code.

    Clients are allowed to render diagnostics with this tag faded out instead of having an error
    squiggle.
    """

    Deprecated = 2
    """
    Deprecated or obsolete code.

    Clients are allowed to rendered diagnostics with this tag strike through.
    """


class MarkupKind(StrEnum):
    """
    Describes the content type that a client supports in various result literals like `Hover`,
    `ParameterInfo` or `CompletionItem`.

    Please note that `MarkupKinds` must not start with a `$`. This kinds are reserved for internal
    usage.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#markupContent
    """

    PlainText = "plaintext"
    """Plain text is supported as a content format."""

    Markdown = "markdown"
    """Markdown is supported as a content format."""


class ResourceOperationKind(StrEnum):
    """
    The kind of resource operations supported by the client.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#resourceOperationKind
    """

    Create = "create"
    """Supports creating new files and folders."""

    Rename = "rename"
    """Supports renaming existing files and folders."""

    Delete = "delete"
    """Supports deleting existing files and folders."""


class FailureHandlingKind(StrEnum):
    """
    The failure handling strategy of a client if applying the workspace edit fails.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#failureHandlingKind
    """

    Abort = "abort"
    """
    Applying the workspace change is simply aborted if one of the changes provided fails. All
    operations executed before the failing operation stay executed.
    """

    Transactional = "transactional"
    """
    All operations are executed transactional. That means they either all succeed or no changes at
    all are applied to the workspace.
    """

    TextOnlyTransactional = "textOnlyTransactional"
    """
    If the workspace edit contains only textual file changes they are executed transactional. If
    resource changes (create, rename or delete file) are part of the change the failure handling
    strategy is abort.
    """

    Undo = "undo"
    """
    The client tries to undo the operations already executed. But there is no guarantee that this
    is succeeding.
    """


class TraceValue(StrEnum):
    """
    A TraceValue represents the level of verbosity with which the server systematically reports its
    execution trace using $/logTrace notifications. The initial trace value is set by the client at
    initialization and can be modified later using the $/setTrace notification.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#traceValue
    """

    Off = "off"
    Messages = "messages"
    Verbose = "verbose"


class InsertTextFormat(IntEnum):
    """
    Defines whether the insert text in a completion item should be interpreted as plain text or a
    snippet.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#insertTextFormat
    """

    PlainText = 1
    """The primary text to be inserted is treated as a plain string."""

    Snippet = 2
    """
    The primary text to be inserted is treated as a snippet.

	A snippet can define tab stops and placeholders with `$1`, `$2` and `${3:foo}`. `$0` defines
    the final tab stop, it defaults to the end of the snippet. Placeholders with equal identifiers
    are linked, that is typing in one will update others too.
    """


class MessageType(IntEnum):
    """
    The type of message for the client to show.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#messageType
    """

    Error = 1
    """An error message."""

    Warning = 2
    """An warning message."""

    Info = 3
    """An information message."""

    Log = 4
    """A log message."""


class SymbolKind(IntEnum):
    """
    A symbol kind.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#symbolKind
    """

    File = 1
    Module = 2
    Namespace = 3
    Package = 4
    Class = 5
    Method = 6
    Property = 7
    Field = 8
    Constructor = 9
    Enum = 10
    Interface = 11
    Function = 12
    Variable = 13
    Constant = 14
    String = 15
    Number = 16
    Boolean = 17
    Array = 18
    Object = 19
    Key = 20
    Null = 21
    EnumMember = 22
    Struct = 23
    Event = 24
    Operator = 25
    TypeParameter = 26


class SymbolTag(IntEnum):
    """
    Symbol tags are extra annotations that tweak the rendering of a symbol.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#symbolTag
    """

    Deprecated = 1
    """
	Render a symbol as obsolete, usually using a strike-out.
    """


class TextDocumentSyncKind(IntEnum):
    """
    Defines how the host (editor) should sync document changes to the language server.

    Values are in CAPS due to None being a keyword and to main consistency.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocumentSyncKind
    """

    NONE = 0
    """Documents should not be synced at all."""

    FULL = 1
    """Documents are synced by always sending the full content of the document."""

    INCREMENTAL = 2
    """
    Documents are synced by sending the full content on open. After that only incremental updates
    to the document are sent.
    """


class TextDocumentSaveReason(IntEnum):
    """
    Represents reasons why a text document is saved.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocumentSaveReason
    """

    Manual = 1
    """
    Manually triggered, e.g. by the user pressing save, by starting debugging, or by an API call.
    """

    AfterDelay = 2
    """Automatic after a delay"""

    FocusOut = 3
    """When the editor lost focus."""


class NotebookCellKind(IntEnum):
    """
    A notebook cell kind.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#notebookCellKind
    """

    Markup = 1
    """
    A markup-cell is formatted source that is used for display.
    """

    Code = 2
    """
    A code-cell is source code.
    """


class DocumentHighlightKind(IntEnum):
    """
    A document highlight kind.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#documentHighlightKind
    """

    Text = 1
    """A textual occurrence."""

    Read = 2
    """Read-access of a symbol, like reading a variable."""

    Write = 3
    """Write-access of a symbol, like writing to a variable."""


class FoldingRangeKind(StrEnum):
    """
    A set of predefined range kinds.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#foldingRangeKind
    """

    Comment = "comment"
    """Folding range for a comment."""

    Imports = "imports"
    """Folding range for imports or includes."""

    Region = "region"
    """Folding range for a region (e.g. `#region`)."""


class SemanticTokenTypes(StrEnum):
    """
    A token type is something like `class` or `function`. The protocol defines a set of token types
    but clients are allowed to extend these and announce the values they support in the
    corresponding client capability.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#semanticTokenTypes
    """

    Namespace = "namespace"
    Type = "type"
    """
    Represents a generic type. Acts as a fallback for types which can't be mapped to a specific
    type like class or enum.
    """
    Class = "class"
    Enum = "enum"
    Interface = "interface"
    Struct = "struct"
    TypeParameter = "typeParameter"
    Parameter = "parameter"
    Variable = "variable"
    Property = "property"
    EnumMember = "enumMember"
    Event = "event"
    Function = "function"
    Method = "method"
    Macro = "macro"
    Keyword = "keyword"
    Modifier = "modifier"
    Comment = "comment"
    String = "string"
    Number = "number"
    Regexp = "regexp"
    Operator = "operator"
    Decorator = "decorator"


class SemanticTokenModifiers(StrEnum):
    """
    A token modifier is something like `static` or `async`. The protocol defines a set of modifiers
    but clients are allowed to extend these and announce the values they support in the
    corresponding client capability.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#semanticTokenModifiers
    """

    Declaration = "declaration"
    Definition = "definition"
    Readonly = "readonly"
    Static = "static"
    Deprecated = "deprecated"
    Abstract = "abstract"
    Async = "async"
    Modification = "modification"
    Documentation = "documentation"
    DefaultLibrary = "defaultLibrary"


class TokenFormat(StrEnum):
    """
    Format of tokens.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#tokenFormat
    """

    Relative = "relative"
    """
    Tokens are described using relative positions (see Integer Encoding for Tokens in
    [Semantic Tokens](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_semanticTokens))
    """


class InlineHintKind(IntEnum):
    """
    Inlay hint kinds.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#inlayHintKind
    """

    Type = 1
    """An inlay hint that for a type annotation."""

    Parameter = 2
    """An inlay hint that is for a parameter."""


class UniquenessLevel(StrEnum):
    """
    Moniker uniqueness level to define scope of the moniker.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#uniquenessLevel
    """

    Document = "document"
    """The moniker is only unique inside a document."""

    Project = "project"
    """The moniker is unique inside a project for which a dump got created."""

    Group = "group"
    """The moniker is unique inside the group to which a project belongs."""

    Scheme = "scheme"
    """The moniker is unique inside the moniker scheme."""

    Global = "global"
    """The moniker is globally unique."""


class MonikerKind(StrEnum):
    """
    The moniker kind.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#monikerKind
    """

    Import = "import"
    """The moniker represent a symbol that is imported into a project."""

    Export = "export"
    """The moniker represents a symbol that is exported from a project."""

    Local = "local"
    """
    The moniker represents a symbol that is local to a project (e.g. a local variable of a
    function, a class not visible outside the project, ...)
    """


class CompletionTriggerKind(IntEnum):
    """
    How a completion was triggered

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#completionTriggerKind
    """

    Invoked = 1
    """
    Completion was triggered by typing an identifier (24x7 code complete), manual invocation (e.g
    Ctrl+Space) or via API.
    """

    TriggerCharacter = 2
    """
    Completion was triggered by a trigger character specified by the `triggerCharacters` properties
    of the `CompletionRegistrationOptions`.
    """

    TriggerForIncompleteCompletions = 3
    """Completion was re-triggered as the current completion list is incomplete."""


class InsertTextMode(IntEnum):
    """
    How whitespace and indentation is handled during completion item insertion.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#insertTextMode
    """

    AsIs = 1
    """
	The insertion or replace strings is taken as it is. If the value is multi line the lines below
    the cursor will be inserted using the indentation defined in the string value.

    The client will not apply any kind of adjustments to the string.
    """

    AdjustIndentation = 2
    """
    The editor adjusts leading whitespace of new lines so that they match the indentation up to the
    cursor of the line for which the item is accepted.

    Consider a line like this: <2tabs><cursor><3tabs>foo. Accepting a multi line completion item is
    indented using 2 tabs and all following lines inserted will be indented using 2 tabs as well.
    """


class DocumentDiagnosticReportKind(StrEnum):
    """
    The document diagnostic report kinds.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#documentDiagnosticReportKind
    """

    Full = "full"
    """A diagnostic report with a full set of problems."""

    Unchanged = "unchanged"
    """A report indicating that the last returned report is still accurate."""


class SignatureHelpTriggerKind(IntEnum):
    """
    How a signature help was triggered.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#signatureHelpTriggerKind
    """

    Invoked = 1
    """Signature help was invoked manually by the user or by a command."""

    TriggerCharacter = 2
    """Signature help was triggered by a trigger character."""

    ContentChange = 3
    """Signature help was triggered by the cursor moving or by the document content changing."""


class CodeActionKind(StrEnum):
    """
    A kind from set of predefined code action kinds.

    Kinds are a hierarchical list of identifiers separated by `.` e.g.
    `"refactor.extract.function"`.

    The set of kinds is open and client needs to announce the kinds it supports to the server
    during initialization.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#codeActionKind
    """

    Empty = ""
    """Empty kind."""

    QuickFix = "quickfix"
    """Base kind for quickfix actions: 'quickfix'."""

    Refactor = "refactor"
    """Base kind for refactoring actions: 'refactor'."""

    RefactorExtract = "refactor.extract"
    """
    Base kind for refactoring extraction actions: 'refactor.extract'.

    Example extract actions:

        - Extract method
    - Extract function
    - Extract variable
    - Extract interface from class
    - ...
    """

    RefactorInline = "refactor.inline"
    """
    Base kind for refactoring inline actions: 'refactor.inline'.

    Example inline actions:

        - Inline function
    - Inline variable
    - Inline constant
    - ...
    """

    RefactorRewrite = "refactor.rewrite"
    """
    Base kind for refactoring rewrite actions: 'refactor.rewrite'.

    Example rewrite actions:

        - Convert JavaScript function to class
    - Add or remove parameter
    - Encapsulate field
    - Make method static
    - Move method to base class
    - ...
    """

    Source = "source"
    """
    Base kind for source actions: `source`.

    Source code actions apply to the entire file.
    """

    SourceOrganizeImports = "source.organizeImports"
    """
    Base kind for an organize imports source action: `source.organizeImports`.
    """

    SourceFixAll = "source.fixAll"
    """
    Base kind for a 'fix all' source action: `source.fixAll`.

    'Fix all' actions automatically fix errors that have a clear fix that
    do not require user input. They should not suppress errors or perform
    unsafe fixes such as generating new types or classes.
    """


class CodeActionTriggerKind(IntEnum):
    """
    The reason why code actions were requested.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#codeActionTriggerKind
    """

    Invoked = 1
    """Code actions were explicitly requested by the user or by an extension."""

    Automatic = 2
    """
    Code actions were requested automatically.

    This typically happens when current selection in a file changes, but can also be triggered when
    file content changes.
    """


class PrepareSupportDefaultBehavior(IntEnum):
    """
    The default rename behavior used by the client.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#prepareSupportDefaultBehavior
    """

    Identifier = 1
    """
    The client's default behavior is to select the identifier according to the language's syntax
    rule.
    """


class FileOperationPatternKind(StrEnum):
    """
    A pattern kind describing if a glob pattern matches a file a folder or both.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#fileOperationPatternKind
    """

    File = "file"
    """The pattern matches a file only."""

    Folder = "folder"
    """The pattern matches a folder only."""


class WatchKind(IntFlag):
    """
    The kind of watch events.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#watchKind
    """

    Create = 1
    """Interested in create events."""

    Change = 2
    """Interested in change events."""

    Delete = 4
    """Interested in delete events."""


class FileChangeType(IntEnum):
    """
    The file event type.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#fileChangeType
    """

    Created = 1
    """The file got created."""

    Changed = 2
    """The file got changed."""

    Deleted = 3
    """The file got deleted."""


class ErrorCodes(IntEnum):
    """
    LSP Error Codes

    Source: https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#errorCodes
    """

    # JSON-RPC error codes
    ParseError = -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603
    # JSON-RPC reserverd error code range
    jsonrpcReservedErrorRangeStart = -32099
    """
    This is the start range of JSON-RPC reserved error codes. It doesn't denote a real error code.
    No LSP error codes should be defined between the start and end range. For backwards
    compatibility the `ServerNotInitialized` and the `UnknownErrorCode` are left in the range.
    """

    jsonrpcReservedErrorRangeEnd = -32000
    """
    This is the end range of JSON-RPC reserved error codes. It doesn't denote a real error code.
    """

    # LSP error codes
    ServerNotInitialized = -32002
    """
    Error code indicating that a server received a notification or request before the server
    received the `initialize` request.
    """

    # UnknownErrorCode for some reason has the same error description as ServerNotInitialized
    UnknownErrorCode = -32001
    """
    Error code indicating that a server received a notification or request before the server
    received the `initialize` request.
    """

    RequestFailed = -32803
    """
    A request failed but it was syntactically correct, e.g the method name was known and the
    parameters were valid. The error message should contain human readable information about why
	the request failed.
    """

    ServerCancelled = -32802
    """
    The server cancelled the request. This error code should only be used for requests that
    explicitly support being server cancellable.
    """

    ContentModified = -32801
    """
	The server detected that the content of a document got modified outside normal conditions. A
    server should NOT send this error code if it detects a content change in its unprocessed
    messages. The result even computed on an older state might still be useful for the client.

	If a client decides that a result is not of any use anymore the client should cancel the
    request.
    """

    RequestCancelled = -32800
    """
    The client has canceled a request and a server has detected the cancel.
    """

    # LSP reserved error range
    lspReservedErrorRangeStart = -32899
    """
    This is the start range of LSP reserved error codes. It doesn't denote a real error code.
    """

    lspReservedErrorRangeEnd = -32800
    """
    This is the end range of LSP reserved error codes. It doesn't denote a real error code.
    """
