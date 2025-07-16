from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_snake
from typing_extensions import TypedDict
from uritools import isuri

import enums

base_config = ConfigDict(alias_generator = to_snake)

Integer = Annotated[int,
                    Field(ge=-2^31, le=2^31-1),
                    """Defines an integer number in the range of -2^31 to 2^31 - 1."""]
UInteger = Annotated[Integer,
                     Field(ge=0),
                     """Defines an unsigned integer number in the range of 0 to 2^31 - 1."""]
Uri = Annotated[str,
                AfterValidator(isuri),
                """
                URI’s are transferred as strings. The URI’s format is defined in https://tools.ietf.org/html/rfc3986

                https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#uri
                """]
LSPAny = Annotated["LSPObject" | "LSPArray" | str | Integer | UInteger | float | bool | None,
                   """
                   The LSP any type.

                   https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#lspAny
                   """]
LSPObject = Annotated[dict[str, LSPAny],
                      """
                      LSP object definition.

                      https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#lspObject
                      """]
LSPArray = Annotated[list[LSPAny],
                     """
                     LSP arrays.

                     https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#lspArray
                     """]
DocumentUri = Annotated[Uri,
                        """
                        Many of the interfaces contain fields that correspond to the URI of a
                        document. For clarity, the type of such a field is declared as a
                        `DocumentUri`. Over the wire, it will still be transferred as a string, but
                        this guarantees that the contents of that string can be parsed as a valid
                        URI.

                        https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#uri
                        """]
ProgressToken = Annotated[str | Integer,
                          """
                          Token associated with each progress report, request, or other
                          communication.

                          https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#progress
                          """]

# NOTE: Both BaseModel and TypedDict are used to explicitely support the faster validation method

class CancelParams(BaseModel, TypedDict):
    """
    The base protocol offers support for request cancellation.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#cancelRequest
    """

    id: Integer | str
    """The request id to cancel."""

class ProgressParams[T](BaseModel, TypedDict):
    """
    The base protocol offers also support to report progress in a generic fashion. This mechanism
    can be used to report any kind of progress including work done progress (usually used to report
    progress in the user interface using a progress bar) and partial result progress to support
    streaming of results.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#progress
    """

    token: Integer | str
    """The progress token provided by the client or server."""

    value: T
    """The progress data."""

class RegularExpressionsClientCapabilities(BaseModel, TypedDict):
    engine: str
    """The engine's name."""

    version: str | None
    """The engine's version."""

class Position(BaseModel, TypedDict):
    """
    Position in a text document expressed as zero-based line and zero-based character offset. A
    position is between two characters like an ‘insert’ cursor in an editor. Special values like
    for example -1 to denote the end of a line are not supported.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#position
    """

    line: UInteger
    """Line position in a document (zero-based)."""

    character: UInteger
    """
    Character offset on a line in a document (zero-based). The meaning of this
	offset is determined by the negotiated `PositionEncodingKind`.

	If the character value is greater than the line length it defaults back
	to the line length.
    """

class Range(BaseModel, TypedDict):
    """
    A range in a text document expressed as (zero-based) start and end positions. A range is
    comparable to a selection in an editor. Therefore, the end position is exclusive. If you want
    to specify a range that contains a line including the line ending character(s) then use an end
    position denoting the start of the next line.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#range
    """

    start: Position
    """The range's start position."""

    end: Position
    """The range's end position."""

class TextDocumentItem(BaseModel, TypedDict):
    """
    An item to transfer a text document from the client to the server.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocumentItem
    """

    uri: DocumentUri
    """The text document's URI."""

    language_id: str
    """The text document's language identifier."""

    version: Integer
    """
    The version number of this document (it will increase after each change, including undo/redo).
    """

    text: str
    """The content of the opened text document."""

    model_config = base_config

class TextDocumentIdentifier(BaseModel, TypedDict):
    """
    Text documents are identified using a URI. On the protocol level, URIs are passed as strings.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocumentIdentifier
    """

    uri: DocumentUri
    """The text document's URI."""


class VersionedTextDocumentIdentifier(TextDocumentIdentifier):
    """
    An identifier to denote a specific version of a text document. This information usually flows
    from the client to the server.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#versionedTextDocumentIdentifier
    """

    version: Integer
    """
    The version number of this document.

	The version number of a document will increase after each change, including undo/redo. The
    number doesn't need to be consecutive.
    """

class OptionalVersionedTextDocumentIdentifier(TextDocumentIdentifier):
    """
    An identifier which optionally denotes a specific version of a text document. This information
    usually flows from the server to the client.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#optionalVersionedTextDocumentIdentifier
    """

    version: Integer | None
    """
    The version number of this document. If an optional versioned text document identifier is sent
    from the server to the client and the file is not open in the editor (the server has not
    received an open notification before) the server can send `null` to indicate that the version
    is known and the content on disk is the master (as specified with document content ownership).

	The version number of a document will increase after each change, including undo/redo. The
    number doesn't need to be consecutive.
    """

class TextDocumentPositionParams(BaseModel, TypedDict):
    """
    A parameter literal used in requests to pass a text document and a position inside that
    document. It is up to the client to decide how a selection is converted into a position when
    issuing a request for a text document. The client can for example honor or ignore the selection
    direction to make LSP request consistent with features implemented internally.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocumentPositionParams
    """

    text_document: TextDocumentIdentifier
    """The text document."""

    position: Position
    """The position inside the text document."""

    model_config = base_config

class DocumentFilter(BaseModel, TypedDict):
    """
    A document filter denotes a document through properties like `language`, `scheme` or `pattern`

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#documentFilter
    """

    language: str | None
    """A language id, like `typescript`."""

    scheme: str | None
    """A Uri scheme, like `file` or `untitled`."""

    pattern: str | None
    """
	A glob pattern, like `*.{ts,js}`.

    Glob patterns can have the following syntax:
    - `*` to match zero or more characters in a path segment
    - `?` to match on one character in a path segment
    - `**` to match any number of path segments, including none
    - `{}` to group sub patterns into an OR expression. (e.g. `**/*.{ts,js}`
        matches all TypeScript and JavaScript files)
    - `[]` to declare a range of characters to match in a path segment
      (e.g., `example.[0-9]` to match on `example.0`, `example.1`, …)
    - `[!...]` to negate a range of characters to match in a path segment
      (e.g., `example.[!0-9]` to match on `example.a`, `example.b`, but
       not `example.0`)
    """

DocumentSelector = Annotated[list[DocumentFilter],
                             """
                             A document selector is the combination of one or more document filters.

                             https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#documentSelector
                             """]

class TextEdit(BaseModel, TypedDict):
    """
    A textual edit applicable to a text document.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textEdit
    """

    range: Range
    """
    The range of the text document to be manipulated. To insert text into a document create a
    range where start === end.
    """

    new_text: str
    """
    The string to be inserted. For delete operations use an empty string.
    """

    model_config = base_config

class ChangeAnnotation(BaseModel, TypedDict):
    """
    Additional information that describes document changes.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#changeAnnotation
    """

    label: str
    """
    A human-readable string describing the actual change. The string is rendered prominent in the
    user interface.
    """

    needs_confirmation: bool | None
    """A flag which indicates that user confirmation is needed before applying the change."""

    description: str | None
    """A human-readable string which is rendered less prominent in the user interface."""

    model_config = base_config

ChangeAnnotationIdentifier = Annotated[str,
                                       """
                                       An identifier referring to a change annotation managed by a
                                       workspace edit.

                                       https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#changeAnnotationIdentifier
                                       """]

class AnnotatedTextEdit(TextEdit):
    """
    A special text edit with an additional change annotation.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#annotatedTextEdit
    """

    annotation_id: ChangeAnnotationIdentifier
    """The actual annotation identifier."""

    model_config = base_config

class TextDocumentEdit(BaseModel, TypedDict):
    """
    Describes textual changes on a single text document. The text document is referred to as a
    `OptionalVersionedTextDocumentIdentifier` to allow clients to check the text document version
    before an edit is applied. A `TextDocumentEdit` describes all changes on a version Si and after
    they are applied move the document to version Si+1. So the creator of a `TextDocumentEdit`
    doesn’t need to sort the array of edits or do any kind of ordering. However the edits must be
    non overlapping.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocumentEdit
    """

    text_document: OptionalVersionedTextDocumentIdentifier
    """The text document to change."""

    edits: list[TextEdit | AnnotatedTextEdit]
    """
    The edits to be applied.
    """

    model_config = base_config

class Location(BaseModel, TypedDict):
    """
    Represents a location inside a resource, such as a line inside a text file.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#location
    """

    uri: DocumentUri

    range: Range

class LocationLink(BaseModel, TypedDict):
    """
    Represents a link between a source and a target location.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#locationLink
    """

    origin_selection_range: Range | None
    """
    Span of the origin of this link.

	Used as the underlined span for mouse interaction. Defaults to the word range at the mouse
    position.
    """

    target_uri: DocumentUri
    """The target resource identifier of this link."""

    target_range: Range
    """
    The full target range of this link. If the target for example is a symbol then target range is
    the range enclosing this symbol not including leading/trailing whitespace but everything else
    like comments. This information is typically used to highlight the range in the editor.
    """

    target_selection_range: Range
    """
    The range that should be selected and revealed when this link is being followed, e.g the name
    of a function. Must be contained by the `targetRange`. See also `DocumentSymbol#range`.
    """

    model_config = base_config

class DiagnosticRelatedInformation(BaseModel, TypedDict):
    """
    Represents a related message and source code location for a diagnostic. This should be used to
    point to code locations that cause or are related to a diagnostics, e.g when duplicating a
    symbol in a scope.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#diagnosticRelatedInformation
    """

    location: Location
    """
    The location of this related diagnostic information.
    """

    message: str
    """
    The message of this related diagnostic information.
    """

class CodeDescription(BaseModel, TypedDict):
    """
    Structure to capture a description for an error code.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#codeDescription
    """

    href: Uri
    """An URI to open with more information about the diagnostic error."""


class Diagnostic(BaseModel, TypedDict):
    range: Range
    """
    The range at which the message applies.
    """

    severity: enums.DiagnosticSeverity | None
    """
    The diagnostic's severity. To avoid interpretation mismatches when a
    server is used with different clients it is highly recommended that
    servers always provide a severity value. If omitted, it’s recommended
    for the client to interpret it as an Error severity.
    """

    code: int | str | None
    """
    The diagnostic's code, which might appear in the user interface.
    """

    code_description: CodeDescription | None
    """
    An optional property to describe the error code.
    """

    source: str | None
    """
    A human-readable string describing the source of this diagnostic, e.g. 'typescript' or
    'super lint'.
    """

    message: str
    """
    The diagnostic's message.
    """

    tags: list[enums.DiagnosticTag] | None
    """
    Additional metadata about the diagnostic.
    """

    related_information: list[DiagnosticRelatedInformation] | None
    """
    An array of related diagnostic information, e.g. when symbol-names within a scope collide all
    definitions can be marked via this property.
    """

    data: LSPAny | None
    """
    A data entry field that is preserved between a `textDocument/publishDiagnostics` notification
    and `textDocument/codeAction` request.
    """

    model_config = base_config

class Command(BaseModel, TypedDict):
    """
    Represents a reference to a command. Provides a title which will be used to represent a
    command in the UI. Commands are identified by a string identifier. The recommended way to
    handle commands is to implement their execution on the server side if the client and server
    provides the corresponding capabilities. Alternatively the tool extension code could handle
    the command. The protocol currently doesn’t specify a set of well-known commands.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#command
    """

    title: str
    """
    Title of the command, like `save`.
    """

    command: str
    """
    The identifier of the actual command handler.
    """

    arguments: list[LSPAny] | None
    """
    Arguments that the command handler should be
    invoked with.
    """

class MarkupContent(BaseModel, TypedDict):
    """
    A `MarkupContent` literal represents a string value which content is
    interpreted base on its kind flag. Currently the protocol supports
    `plaintext` and `markdown` as markup kinds.

    If the kind is `markdown` then the value can contain fenced code blocks like
    in GitHub issues.

    Here is an example how such a string can be constructed using
    JavaScript / TypeScript:
    ```typescript
    let markdown: MarkdownContent = {
        kind: MarkupKind.Markdown,
        value: [
            '# Header',
            'Some text',
            '```typescript',
            'someCode();',
            '```'
        ].join('\n')
    };
    ```

    *Please Note* that clients might sanitize the return markdown. A client could
    decide to remove HTML from the markdown to avoid script execution.
    """

    kind: enums.MarkupKind
    """
    The type of the Markup
    """

    value: str
    """
    The content itself
    """

class MarkdownClientCapabilities(BaseModel, TypedDict):
    """
    Client capabilities specific to the used markdown parser.
    """

    parser: str
    """
    The name of the parser.
    """

    version: str | None
    """
    The version of the parser.
    """

    allowed_tags: list[str] | None
    """
    A list of HTML tags that the client allows / supports in Markdown.
    """

    model_config = base_config

class CreateFileOptions(BaseModel, TypedDict):
    """
    Options to create a file.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#createFileOptions
    """

    overwrite: bool | None
    """
    Overwrite existing file. Overwrite wins over `ignoreIfExists`
    """

    ignore_if_exists: bool | None
    """
    Ignore if exists.
    """

    model_config = base_config

class RenameFileOptions(BaseModel, TypedDict):
    """
    Rename file options

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#createFileOptions
    """

    overwrite: bool | None
    """
    Overwrite target if existing. Overwrite wins over `ignoreIfExists`
    """

    ignore_if_exists: bool | None
    """
    Ignores if target exists.
    """

    model_config = base_config

class DeleteFileOptions(BaseModel, TypedDict):
    """
    Delete file options

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#deleteFileOptions
    """

    recursive: bool | None
    """
    Delete the content recursively if a folder is denoted.
    """

    ignore_if_not_exists: bool | None
    """
    Ignore the operation if the file doesn't exist.
    """

    model_config = base_config

class CreateFile(BaseModel, TypedDict):
    """
    Create file operation

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#createFile
    """

    kind: Literal["create"]
    """
    A create
    """

    uri: DocumentUri
    """
    The resource to create.
    """

    options: CreateFileOptions | None
    """
    Additional options
    """

    annotation_id: ChangeAnnotationIdentifier | None
    """
    An optional annotation identifier describing the operation.
    """

    model_config = base_config

class RenameFile(BaseModel, TypedDict):
    """
    Rename file operation

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#renameFile
    """

    kind: Literal["rename"]
    """
    A rename
    """

    old_uri: DocumentUri
    """
    The old (existing) location.
    """

    new_uri: DocumentUri
    """
    The new location.
    """

    options: RenameFileOptions | None
    """
    Rename options.
    """

    annotation_id: ChangeAnnotationIdentifier | None
    """
    An optional annotation identifier describing the operation.
    """

    model_config = base_config

class DeleteFile(BaseModel, TypedDict):
    """
    Delete file operation

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#deleteFile
    """

    kind: Literal["delete"]
    """
    A delete
    """

    uri: DocumentUri
    """
    The file to delete.
    """

    options: DeleteFileOptions | None
    """
    Delete options.
    """

    annotation_id: ChangeAnnotationIdentifier | None
    """
    An optional annotation identifier describing the operation.
    """

    model_config = base_config

class WorkspaceEdit(BaseModel, TypedDict):
    """
    Workspace edit

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspaceEdit
    """

    changes: dict[DocumentUri, list[TextEdit]] | None
    """
    Holds changes to existing resources.
    """

    document_changes: (
        list[TextDocumentEdit] |
        list[TextDocumentEdit | CreateFile | RenameFile | DeleteFile] |
        None
    )
    """
    Depending on the client capability
    `workspace.workspaceEdit.resourceOperations` document changes are either
    an array of `TextDocumentEdit`s to express changes to n different text
    documents where each text document edit addresses a specific version of
    a text document. Or it can contain above `TextDocumentEdit`s mixed with
    create, rename and delete file / folder operations.

    Whether a client supports versioned document edits is expressed via
    `workspace.workspaceEdit.documentChanges` client capability.

    If a client neither supports `documentChanges` nor
    `workspace.workspaceEdit.resourceOperations` then only plain `TextEdit`s
    using the `changes` property are supported.
    """

    change_annotations: dict[str, ChangeAnnotation] | None
    """
    A map of change annotations that can be referenced in
    `AnnotatedTextEdit`s or create, rename and delete file / folder
    operations.

    Whether clients honor this property depends on the client capability
    `workspace.changeAnnotationSupport`.
    """

    model_config = base_config


class WorkspaceEditClientCapabilities(BaseModel, TypedDict):
    """
    Workspace edit client capabilities

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspaceEditClientCapabilities
    """

    document_changes: bool | None
    """
    The client supports versioned document changes in `WorkspaceEdit`s
    """

    resource_operations: list[enums.ResourceOperationKind] | None
    """
    The resource operations the client supports. Clients should at least
    support 'create', 'rename' and 'delete' files and folders.
    """

    failure_handling: enums.FailureHandlingKind | None
    """
    The failure handling strategy of a client if applying the workspace edit
    fails.
    """

    normalizes_line_endings: bool | None
    """
    Whether the client normalizes line endings to the client specific
    setting.
    If set to `true` the client will normalize line ending characters
    in a workspace edit to the client specific new line character(s).
    """

    change_annotation_support: dict[str, bool] | None
    """
    Whether the client in general supports change annotations on text edits,
    create file, rename file and delete file changes.

    Properties:
        groupsOnLabel?: Whether the client groups edits with equal labels into tree nodes,
        for instance all edits labelled with "Changes in Strings" would be a tree node.
    """

    model_config = base_config

class WorkDoneProgressBegin(BaseModel, TypedDict):
    """
    Begin progress operation

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workDoneProgressBegin
    """

    kind: Literal['begin']
    """
    Kind of progress operation
    """

    title: str
    """
    Mandatory title of the progress operation. Used to briefly inform about
    the kind of operation being performed.

    Examples: "Indexing" or "Linking dependencies".
    """

    cancellable: bool | None
    """
    Controls if a cancel button should show to allow the user to cancel the
    long running operation. Clients that don't support cancellation are
    allowed to ignore the setting.
    """

    message: str | None
    """
    Optional, more detailed associated progress message. Contains
    complementary information to the `title`.

    Examples: "3/25 files", "project/src/module2", "node_modules/some_dep".
    If unset, the previous progress message (if any) is still valid.
    """

    percentage: UInteger | None
    """
    Optional progress percentage to display (value 100 is considered 100%).
    If not provided infinite progress is assumed and clients are allowed
    to ignore the `percentage` value in subsequent report notifications.

    The value should be steadily rising. Clients are free to ignore values
    that are not following this rule. The value range is [0, 100].
    """

class WorkDoneProgressReport(BaseModel, TypedDict):
    """
    Report progress operation

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workDoneProgressReport
    """

    kind: Literal['report']
    """
    Kind of progress operation
    """

    cancellable: bool | None
    """
    Controls enablement state of a cancel button. This property is only valid
    if a cancel button got requested in the `WorkDoneProgressBegin` payload.

    Clients that don't support cancellation or don't support control the
    button's enablement state are allowed to ignore the setting.
    """

    message: str | None
    """
    Optional, more detailed associated progress message. Contains
    complementary information to the `title`.

    Examples: "3/25 files", "project/src/module2", "node_modules/some_dep".
    If unset, the previous progress message (if any) is still valid.
    """

    percentage: UInteger | None
    """
    Optional progress percentage to display (value 100 is considered 100%).
    If not provided infinite progress is assumed and clients are allowed
    to ignore the `percentage` value in subsequent report notifications.

    The value should be steadily rising. Clients are free to ignore values
    that are not following this rule. The value range is [0, 100].
    """

class WorkDoneProgressEnd(BaseModel, TypedDict):
    """
    End progress operation

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workDoneProgressEnd
    """

    kind: Literal['end']
    """
    Kind of progress operation
    """

    message: str | None
    """
    Optional, a final message indicating to for example indicate the outcome
    of the operation.
    """

class WorkDoneProgressParams(BaseModel, TypedDict):
    """
    Work done progress parameters

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workDoneProgressParams
    """

    work_done_token: ProgressToken | None
    """
    An optional token that a server can use to report work done progress.
    """

    model_config = base_config

class PartialResultParams(BaseModel, TypedDict):
    """
    Partial result parameters

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#partialResultParams
    """

    partial_result_token: ProgressToken | None
    """
    An optional token that a server can use to report partial results (e.g.
    streaming) to the client.
    """

    model_config = base_config

class ClientInfo(BaseModel, TypedDict):
    """
    Information about the client

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#initializeParams
    """
    name: str
    """
    The name of the client as defined by the client.
    """

    version: str | None
    """
    The client's version as defined by the client.
    """

class WorkspaceFolder(BaseModel, TypedDict):
    """
    A workspace folder.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspaceFolder
    """

    uri: Uri
    """
    The associated URI for this workspace folder.
    """

    name: str
    """
    The name of the workspace folder. Used to refer to this
    workspace folder in the user interface.
    """

class TextDocumentSyncClientCapabilities(BaseModel, TypedDict):
    """
    Text document specific client capabilities.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocumentClientCapabilities
    """

    dynamic_registration: bool | None
    """Whether text document synchronization supports dynamic registration."""

    will_save: bool | None
    """The client supports sending will save notifications."""

    will_save_wait_until: bool | None
    """The client supports sending a will save request and
    waits for a response providing text edits which will
    be applied to the document before it is saved."""

    did_save: bool | None
    """The client supports did save notifications."""

    model_config = base_config

class TagSupportProperty(BaseModel, TypedDict):
    value_set: list[enums.CompletionItemTag]
    """The tags supported by the client."""

    model_config = base_config

class InsertTextModeSupport(BaseModel, TypedDict):
    """The client supports the `insertTextMode` property on
    a completion item to override the whitespace handling mode
    as defined by the client (see `insertTextMode`).

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#completionClientCapabilities
    """

    value_set: list[enums.InsertTextMode]

    model_config = base_config

class CompletionItemResolveSupport(BaseModel, TypedDict):
    """
    Indicates which properties a client can resolve lazily on a
	completion item. Before version 3.16.0 only the predefined properties
	`documentation` and `detail` could be resolved lazily.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#completionClientCapabilities
    """

    properties: list[str]
    """The properties that a client can resolve lazily."""

class CompletionItemCapabilities(BaseModel, TypedDict):
    """
    The client supports the following `CompletionItem` specific capabilities.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#completionClientCapabilities
    """

    snippet_support: bool | None
    """
    Client supports snippets as insert text.

    A snippet can define tab stops and placeholders with `$1`, `$2`
    and `${3:foo}`. `$0` defines the final tab stop, it defaults to
    the end of the snippet. Placeholders with equal identifiers are
    linked, that is typing in one will update others too.
    """

    commit_characters_support: bool | None
    """Client supports commit characters on a completion item."""

    documentation_format: list[enums.MarkupKind] | None
    """Client supports the follow content formats for the documentation
    property. The order describes the preferred format of the client."""

    deprecated_support: bool | None
    """Client supports the deprecated property on a completion item."""

    preselect_support: bool | None
    """Client supports the preselect property on a completion item."""

    tag_support: TagSupportProperty | None
    """
    Client supports the tag property on a completion item. Clients
    supporting tags have to handle unknown tags gracefully. Clients
    especially need to preserve unknown tags when sending a completion
    item back to the server in a resolve call.
    """

    insert_replace_support: bool | None
    """
    Client supports insert replace edit to control different behavior if
    a completion item is inserted in the text or should replace text.
    """

    resolve_support: CompletionItemResolveSupport | None
    """
    Indicates which properties a client can resolve lazily on a
    completion item. Before version 3.16.0 only the predefined properties
    `documentation` and `detail` could be resolved lazily.
    """

    insert_text_mode_support: InsertTextModeSupport | None
    """
    The client supports the `insertTextMode` property on
    a completion item to override the whitespace handling mode
    as defined by the client (see `insertTextMode`).
    """

    label_details_support: bool | None
    """
    The client has support for completion item label
    details (see also `CompletionItemLabelDetails`).
    """

    model_config = base_config

class CompletionItemKindCapabilities(BaseModel, TypedDict):
    """
    The completion item kind values the client supports. When this
    property exists the client also guarantees that it will
    handle values outside its set gracefully and falls back
    to a default value when unknown.

    If this property is not present the client only supports
    the completion items kinds from `Text` to `Reference` as defined in
    the initial version of the protocol.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#completionClientCapabilities
    """

    value_set: list[enums.CompletionItemKind] | None

    model_config = base_config

class CompletionListCapabilities(BaseModel, TypedDict):
    """
    The client supports the following `CompletionList` specific capabilities.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#completionClientCapabilities
    """

    item_defaults: list[str] | None
    """
    The client supports the following itemDefaults on
    a completion list.

    The value lists the supported property names of the
    `CompletionList.itemDefaults` object. If omitted
    no properties are supported.
    """

    model_config = base_config

class CompletionClientCapabilities(BaseModel, TypedDict):
    """
    Features and capabilities that the client supports in regards to completion.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#completionClientCapabilities
    """

    dynamic_registration: bool | None
    """
    Whether completion supports dynamic registration.
    """

    completion_item: CompletionItemCapabilities | None
    """
    The client supports the following `CompletionItem` specific capabilities.
    """

    completion_item_kind: CompletionItemKindCapabilities | None
    """
    The completion item kind values the client supports. When this property exists the client also
    guarantees that it will handle values outside its set gracefully and falls back to a default
    value when unknown.

    If this property is not present the client only supports the completion items kinds from `Text`
    to `Reference` as defined in the initial version of the protocol.
    """

    context_support: bool | None
    """
    The client supports to send additional context information for a `textDocument/completion`
    request.
    """

    insert_text_mode: enums.InsertTextMode | None
    """
    The client's default when the completion item doesn't provide a `insertTextMode` property.
    """

    completion_list: CompletionListCapabilities | None
    """
    The client supports the following `CompletionList` specific capabilities.
    """

    model_config = base_config

class HoverClientCapabilities(BaseModel, TypedDict):
    """
    What capabilities the client supports for hover methods/operations.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#hoverClientCapabilities
    """

    dynamic_registration: bool | None
    """Whether hover supports dynamic registration."""

    content_format: list[enums.MarkupKind] | None
    """
    Client supports the follow content formats if the content property refers to a `literal of
    type MarkupContent`. The order describes the preferred format of the client.
    """

    model_config = base_config

class ParameterInformationCapabilities(BaseModel, TypedDict):
    """
    Client capabilities specific to parameter information.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#signatureHelpClientCapabilities
    """

    label_offset_support: bool | None
    """
    The client supports processing label offsets instead of a simple label string.
    """

    model_config = base_config


class SignatureInformationCapabilities(BaseModel, TypedDict):
    """
    The client supports the following `SignatureInformation` specific properties.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#signatureHelpClientCapabilities
    """

    documentation_format: list[enums.MarkupKind] | None
    """
    Client supports the follow content formats for the documentation property. The order describes
    the preferred format of the client.
    """

    parameter_information: ParameterInformationCapabilities | None
    """Client capabilities specific to parameter information."""

    active_parameter_support: bool | None
    """
    The client supports the `activeParameter` property on `SignatureInformation` literal.
    """

    model_config = base_config

class SignatureHelpClientCapabilities(BaseModel, TypedDict):
    """
    The clients capabilities in regards to signature help.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#signatureHelpClientCapabilities
    """

    dynamic_registration: bool | None
    """Whether signature help supports dynamic registration."""

    signature_information: SignatureInformationCapabilities | None
    """
    The client supports the following `SignatureInformation` specific properties.
    """

    context_support: bool | None
    """
    The client supports to send additional context information for a `textDocument/signatureHelp`
    request. A client that opts into contextSupport will also support the `retriggerCharacters` on
    `SignatureHelpOptions`.
    """

    model_config = base_config

class DeclarationClientCapabilities(BaseModel, TypedDict):
    """
    The clients capabilites in regards to declarations of symbols.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#declarationClientCapabilities
    """

    dynamic_registration: bool | None
    """
    Whether declaration supports dynamic registration. If this is set to `true` the client
    supports the new `DeclarationRegistrationOptions` return value for the corresponding server
    capability as well.
    """

    link_support: bool | None
    """The client supports additional metadata in the form of declaration links."""

    model_config = base_config

class DefinitionClientCapabilities(BaseModel, TypedDict):
    """
    The clients capabilites in regards to definition of symbols.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#definitionClientCapabilities
    """

    dynamic_registration: bool | None
    """Whether definition supports dynamic registration."""

    link_support: bool | None
    """The client supports additional metadata in the form of definition links."""

    model_config = base_config

class TypeDefinitionClientCapabilities(BaseModel, TypedDict):
    """
    The clients capabilites in regards to type definition of symbols.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#typeDefinitionClientCapabilities
    """

    dynamic_registration: bool | None
    """
    Whether implementation supports dynamic registration. If this is set to `true` the client
    supports the new `TypeDefinitionRegistrationOptions` return value for the corresponding server
    capability as well.
    """

    link_support: bool | None
    """The client supports additional metadata in the form of definition links."""

    model_config = base_config

class ImplementationClientCapabilities(BaseModel, TypedDict):
    """
    The clients capabilites in regards to implementation of symbols.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#implementationClientCapabilities
    """

    dynamic_registration: bool | None
    """
    Whether implementation supports dynamic registration. If this is set to `true` the client
    supports the new `ImplementationRegistrationOptions` return value for the corresponding server
    capability as well.
    """

    link_support: bool | None
    """The client supports additional metadata in the form of definition links."""

    model_config = base_config

class ReferenceClientCapabilities(BaseModel, TypedDict):
    """
    The clients capabilites in regards to project-wide references of symbols.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#referenceClientCapabilities
    """

    dynamic_registration: bool | None
    """Whether references supports dynamic registration."""

    model_config = base_config

class DocumentHighlightClientCapabilities(BaseModel, TypedDict):
    """
    The clients capabilites in regards to document highlights.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#documentHighlightClientCapabilities
    """

    dynamic_registration: bool
    """Whether document highlight supports dynamic registration."""

    model_config = base_config

class SymbolKindProperty(BaseModel, TypedDict, total=False):
    value_set: list[enums.SymbolKind]
    """
    The symbol kind values the client supports. When this
    property exists the client also guarantees that it will
    handle values outside its set gracefully and falls back
    to a default value when unknown.

    If this property is not present the client only supports
    the symbol kinds from `File` to `Array` as defined in
    the initial version of the protocol.
    """

    model_config = base_config

class DocumentSymbolClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#documentSymbolClientCapabilities
    """

    dynamic_registration: bool
    """Whether document symbol supports dynamic registration."""

    symbol_kind: SymbolKindProperty
    """Specific capabilities for the `SymbolKind` in the `textDocument/documentSymbol` request."""

    hierarchical_document_symbol_support: bool
    """The client supports hierarchical document symbols."""

    tag_support: TagSupportProperty
    """
    The client supports tags on `SymbolInformation`. Tags are supported on
    `DocumentSymbol` if `hierarchicalDocumentSymbolSupport` is set to true.
    Clients supporting tags have to handle unknown tags gracefully.
    """

    label_support: bool
    """
    The client supports an additional label presented in the UI when
    registering a document symbol provider.
    """

    model_config = base_config

class ResolveSupportProperty(BaseModel, TypedDict):
    properties: list[str]
    """
    The properties that a client can resolve lazily.
    """

    model_config = base_config

class CodeActionKindSupportProperty(BaseModel, TypedDict):
    value_set: list[enums.CodeActionKind]
    """
    The code action kind values the client supports. When this
    property exists the client also guarantees that it will
    handle values outside its set gracefully and falls back
    to a default value when unknown.
    """

    model_config = base_config


class CodeActionLiteralSupportProperty(BaseModel, TypedDict):
    code_action_kind: CodeActionKindSupportProperty
    """
    The code action kind is supported with the following value set.
    """

    model_config = base_config


class CodeActionClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#codeActionClientCapabilities
    """

    dynamic_registration: bool
    """
    Whether code action supports dynamic registration.
    """

    code_action_literal_support: CodeActionLiteralSupportProperty
    """
    The client supports code action literals as a valid response of the
    `textDocument/codeAction` request.
    """

    is_preferred_support: bool
    """
    Whether code action supports the `isPreferred` property.
    """

    disabled_support: bool
    """
    Whether code action supports the `disabled` property.
    """

    data_support: bool
    """
    Whether code action supports the `data` property which is preserved
    between a `textDocument/codeAction` and a `codeAction/resolve` request.
    """

    resolve_support: ResolveSupportProperty
    """
    Whether the client supports resolving additional code action properties
    via a separate `codeAction/resolve` request.
    """

    honors_change_annotations: bool
    """
    Whether the client honors the change annotations in text edits and
    resource operations returned via the `CodeAction#edit` property by for
    example presenting the workspace edit in the user interface and asking
    for confirmation.
    """

    model_config = base_config

class CodeLensClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#codeLensClientCapabilities
    """

    dynamic_registration: bool
    """
    Whether code lens supports dynamic registration.
    """

    model_config = base_config

class DocumentLinkClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#documentLinkClientCapabilities
    """

    dynamic_registration: bool
    """
    Whether document link supports dynamic registration.
    """

    tooltip_support: bool
    """
    Whether the client supports the `tooltip` property on `DocumentLink`.
    """

    model_config = base_config

class DocumentColorClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#documentColorClientCapabilities
    """

    dynamic_registration: bool
    """
    Whether document color supports dynamic registration.
    """

    model_config = base_config

class DocumentFormattingClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#documentFormattingClientCapabilities
    """

    dynamic_registration: bool
    """
    Whether formatting supports dynamic registration.
    """

    model_config = base_config

class DocumentRangeFormattingClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#documentRangeFormattingClientCapabilities
    """

    dynamic_registration: bool
    """
    Whether formatting supports dynamic registration.
    """

    model_config = base_config

class DocumentOnTypeFormattingClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#documentOnTypeFormattingClientCapabilities
    """

    dynamic_registration: bool
    """
    Whether on type formatting supports dynamic registration.
    """

    model_config = base_config

class RenameClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#renameClientCapabilities
    """

    dynamic_registration: bool
    """
    Whether rename supports dynamic registration.
    """

    prepare_support: bool
    """
    Client supports testing for validity of rename operations
    before execution.
    """

    prepare_support_default_behavior: enums.PrepareSupportDefaultBehavior
    """
    Client supports the default behavior result
    (`{ defaultBehavior: boolean }`).

    The value indicates the default behavior used by the
    client.
    """

    honors_change_annotations: bool
    """
    Whether the client honors the change annotations in
    text edits and resource operations returned via the
    rename request's workspace edit by for example presenting
    the workspace edit in the user interface and asking
    for confirmation.
    """

    model_config = base_config

class PublishDiagnosticsClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#publishDiagnosticsClientCapabilities
    """

    related_information: bool
    """
    Whether the clients accepts diagnostics with related information.
    """

    tag_support: TagSupportProperty
    """
    Client supports the tag property to provide meta data about a diagnostic.
    Clients supporting tags have to handle unknown tags gracefully.
    """

    version_support: bool
    """
    Whether the client interprets the version property of the
    `textDocument/publishDiagnostics` notification's parameter.
    """

    code_description_support: bool
    """
    Client supports a codeDescription property
    """

    data_support: bool
    """
    Whether code action supports the `data` property which is
    preserved between a `textDocument/publishDiagnostics` and
    `textDocument/codeAction` request.
    """

    model_config = base_config

class FoldingRangeKindProperty(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#foldingRangeClientCapabilities
    """
    
    value_set: list[enums.FoldingRangeKind] | None
    """
    The folding range kind values the client supports. When this
    property exists the client also guarantees that it will
    handle values outside its set gracefully and falls back
    to a default value when unknown.
    """

    model_config = base_config

class FoldingRangeOptions(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#foldingRangeClientCapabilities
    """
    
    collapsed_text: bool | None
    """
    If set, the client signals that it supports setting collapsedText on
    folding ranges to display custom labels instead of the default text.
    """

    model_config = base_config

class FoldingRangeClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#foldingRangeClientCapabilities
    """

    dynamic_registration: bool | None
    """
    Whether implementation supports dynamic registration for folding range
    providers. If this is set to `true` the client supports the new
    `FoldingRangeRegistrationOptions` return value for the corresponding
    server capability as well.
    """

    range_limit: int | None
    """
    The maximum number of folding ranges that the client prefers to receive
    per document. The value serves as a hint, servers are free to follow the
    limit.
    """

    line_folding_only: bool | None
    """
    If set, the client signals that it only supports folding complete lines.
    If set, client will ignore specified `startCharacter` and `endCharacter`
    properties in a FoldingRange.
    """

    folding_range_kind: FoldingRangeKindProperty | None
    """
    Specific options for the folding range kind.
    """

    folding_range: FoldingRangeOptions | None
    """
    Specific options for the folding range.
    """

    model_config = base_config

class SelectionRangeClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#selectionRangeClientCapabilities
    """

    dynamic_registration: bool | None
    """
    Whether implementation supports dynamic registration for selection range
    providers. If this is set to `true` the client supports the new
    `SelectionRangeRegistrationOptions` return value for the corresponding
    server capability as well.
    """

    model_config = base_config

class LinkedEditingRangeClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#linkedEditingRangeClientCapabilities
    """

    dynamic_registration: bool | None
    """
    Whether the implementation supports dynamic registration.
    If this is set to `true` the client supports the new
    `(TextDocumentRegistrationOptions & StaticRegistrationOptions)`
    return value for the corresponding server capability as well.
    """

    model_config = base_config

class CallHierarchyClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#callHierarchyClientCapabilities
    """

    dynamic_registration: bool | None
    """
    Whether implementation supports dynamic registration. If this is set to
    `true` the client supports the new `(TextDocumentRegistrationOptions &
    StaticRegistrationOptions)` return value for the corresponding server
    capability as well.
    """

    model_config = base_config

class SemanticTokensClientCapabilitiesRequestsFull(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#semanticTokensClientCapabilities
    """

    delta: bool | None
    """
    The client will send the `textDocument/semanticTokens/full/delta`
    request if the server provides a corresponding handler.
    """

class SemanticTokensClientCapabilitiesRequests(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#semanticTokensClientCapabilities
    """

    range: bool | dict | None
    """
    The client will send the `textDocument/semanticTokens/range` request
    if the server provides a corresponding handler.
    """
    full: bool | SemanticTokensClientCapabilitiesRequestsFull | None
    """
    The client will send the `textDocument/semanticTokens/full` request
    if the server provides a corresponding handler.
    """

class SemanticTokensClientCapabilities(BaseModel, TypedDict, total=False):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#semanticTokensClientCapabilities
    """

    dynamic_registration: bool | None
    """
    Whether implementation supports dynamic registration. If this is set to
    `true` the client supports the new `(TextDocumentRegistrationOptions &
    StaticRegistrationOptions)` return value for the corresponding server
    capability as well.
    """

    requests: SemanticTokensClientCapabilitiesRequests
    """
    Which requests the client supports and might send to the server
    depending on the server's capability. Please note that clients might not
    show semantic tokens or degrade some of the user experience if a range
    or full request is advertised by the client but not provided by the
    server.
    """

    token_types: list[str]
    """
    The token types that the client supports.
    """

    token_modifiers: list[str]
    """
    The token modifiers that the client supports.
    """

    formats: list[enums.TokenFormat]
    """
    The formats the clients supports.
    """

    overlapping_token_support: bool | None
    """
    Whether the client supports tokens that can overlap each other.
    """

    multiline_token_support: bool | None
    """
    Whether the client supports tokens that can span multiple lines.
    """

    server_cancel_support: bool | None
    """
    Whether the client allows the server to actively cancel a
    semantic token request.
    """

    augments_syntax_tokens: bool | None
    """
    Whether the client uses semantic tokens to augment existing
    syntax tokens.
    """

    model_config = base_config

class MonikerClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#monikerClientCapabilities
    """

    dynamic_registration: bool | None
    """
    Whether implementation supports dynamic registration. If this is set to
    `true` the client supports the new `(TextDocumentRegistrationOptions &
    StaticRegistrationOptions)` return value for the corresponding server
    capability as well.
    """

    model_config = base_config

class TypeHierarchyClientCapabilities(BaseModel, TypedDict):
    """
    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#typeHierarchyClientCapabilities
    """

    dynamic_registration: bool | None
    """
    Whether implementation supports dynamic registration. If this is set to
    `true` the client supports the new `(TextDocumentRegistrationOptions &
    StaticRegistrationOptions)` return value for the corresponding server
    capability as well.
    """

    model_config = base_config

class InlineValueClientCapabilities(BaseModel, TypedDict, total=False):
    """
    Client capabilities specific to inline values.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#inlineValueClientCapabilities
    """

    dynamic_registration: bool | None
    """
    Whether implementation supports dynamic registration for inline
    value providers.
    """

    model_config = base_config

class InlayHintClientCapabilities(BaseModel, TypedDict, total=False):
    """
    Inlay hint client capabilities.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#inlayHintClientCapabilities
    """

    dynamic_registration: bool | None
    """
    Whether inlay hints support dynamic registration.
    """

    resolve_support: ResolveSupportProperty | None
    """
    Indicates which properties a client can resolve lazily on an inlay hint.
    """

    model_config = base_config

class DiagnosticClientCapabilities(BaseModel, TypedDict, total=False):
    """
    Client capabilities specific to diagnostic pull requests.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#diagnosticClientCapabilities
    """

    dynamic_registration: bool | None
    """
    Whether implementation supports dynamic registration. If this is set to
    `true` the client supports the new
    `(TextDocumentRegistrationOptions & StaticRegistrationOptions)`
    return value for the corresponding server capability as well.
    """

    related_document_support: bool | None
    """
    Whether the clients supports related documents for document diagnostic
    pulls.
    """

    model_config = base_config

class TextDocumentClientCapabilities(BaseModel, TypedDict):
    """
    Text document specific client capabilities.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocumentClientCapabilities
    """

    synchronization: TextDocumentSyncClientCapabilities | None

    completion: CompletionClientCapabilities | None
    """Capabilities specific to the `textDocument/completion` request."""

    hover: HoverClientCapabilities | None
    """Capabilities specific to the `textDocument/hover` request."""

    signature_help: SignatureHelpClientCapabilities | None
    """Capabilities specific to the `textDocument/signatureHelp` request."""

    declaration: DeclarationClientCapabilities | None
    """Capabilities specific to the `textDocument/declaration` request."""

    definition: DefinitionClientCapabilities | None
    """Capabilities specific to the `textDocument/definition` request."""

    type_definition: TypeDefinitionClientCapabilities | None
    """Capabilities specific to the `textDocument/typeDefinition` request."""

    implementation: ImplementationClientCapabilities | None
    """Capabilities specific to the `textDocument/implementation` request."""

    references: ReferenceClientCapabilities | None
    """Capabilities specific to the `textDocument/references` request."""

    document_highlight: DocumentHighlightClientCapabilities | None
    """Capabilities specific to the `textDocument/documentHighlight` request."""

    document_symbol: DocumentSymbolClientCapabilities | None
    """Capabilities specific to the `textDocument/documentSymbol` request."""

    code_action: CodeActionClientCapabilities | None
    """Capabilities specific to the `textDocument/codeAction` request."""

    code_lens: CodeLensClientCapabilities | None
    """Capabilities specific to the `textDocument/codeLens` request."""

    document_link: DocumentLinkClientCapabilities | None
    """Capabilities specific to the `textDocument/documentLink` request."""

    color_provider: DocumentColorClientCapabilities | None
    """
    Capabilities specific to the `textDocument/documentColor` and the
    `textDocument/colorPresentation` request.
    """

    formatting: DocumentFormattingClientCapabilities | None
    """Capabilities specific to the `textDocument/formatting` request."""

    range_formatting: DocumentRangeFormattingClientCapabilities | None
    """Capabilities specific to the `textDocument/rangeFormatting` request."""

    on_type_formatting: DocumentOnTypeFormattingClientCapabilities | None
    """Capabilities specific to the `textDocument/onTypeFormatting` request."""

    rename: RenameClientCapabilities | None
    """Capabilities specific to the `textDocument/rename` request."""

    publish_diagnostics: PublishDiagnosticsClientCapabilities | None
    """
    Capabilities specific to the `textDocument/publishDiagnostics` notification.
    """

    folding_range: FoldingRangeClientCapabilities | None
    """Capabilities specific to the `textDocument/foldingRange` request."""

    selection_range: SelectionRangeClientCapabilities | None
    """Capabilities specific to the `textDocument/selectionRange` request."""

    linked_editing_range: LinkedEditingRangeClientCapabilities | None
    """Capabilities specific to the `textDocument/linkedEditingRange` request."""

    call_hierarchy: CallHierarchyClientCapabilities | None
    """Capabilities specific to the various call hierarchy requests."""

    semantic_tokens: SemanticTokensClientCapabilities | None
    """Capabilities specific to the various semantic token requests."""

    moniker: MonikerClientCapabilities | None
    """Capabilities specific to the `textDocument/moniker` request."""

    type_hierarchy: TypeHierarchyClientCapabilities | None
    """Capabilities specific to the various type hierarchy requests."""

    inline_value: InlineValueClientCapabilities | None
    """Capabilities specific to the `textDocument/inlineValue` request."""

    inlay_hint: InlayHintClientCapabilities | None
    """Capabilities specific to the `textDocument/inlayHint` request."""

    diagnostic: DiagnosticClientCapabilities | None
    """Capabilities specific to the diagnostic pull model."""

    model_config = base_config

class DidChangeConfigurationClientCapabilities(BaseModel, TypedDict):
    """
    Did change configuration notification client capabilities.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#didChangeConfigurationClientCapabilities
    """

    dynamic_registration: bool
    """Did change configuration notification supports dynamic registration."""

    model_config = base_config

class DidChangeWatchedFilesClientCapabilities(BaseModel, TypedDict):
    """
    Did change watched files notification client capabilities.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#didChangeWatchedFilesClientCapabilities
    """

    dynamic_registration: bool
    """
    Did change watched files notification supports dynamic registration. Please note that the
    current protocol doesn't support static configuration for file changes from the server side.
    """

    relative_pattern_support: bool
    """Whether the client has support for relative patterns or not."""

    model_config = base_config

class WorkspaceSymbolClientCapabilities(BaseModel, TypedDict):
    """
    Workspace symbol client capabilities.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_symbol
    """

    dynamic_registration: bool
    """Symbol request supports dynamic registration."""

    symbol_kind: SymbolKindProperty
    """Specific capabilities for the `SymbolKind` in the `workspace/symbol` request."""

    tag_support: TagSupportProperty
    """
    The client supports tags on `SymbolInformation` and `WorkspaceSymbol`. Clients supporting tags
    have to handle unknown tags gracefully.
    """

    resolve_support: ResolveSupportProperty
    """
    The client support partial workspace symbols. The client will send the request
    `workspaceSymbol/resolve` to the server to resolve additional properties.
    """

    model_config = base_config

class ExecuteCommandClientCapabilities(BaseModel, TypedDict):
    """
    Execute command client capabilities.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#executeCommandClientCapabilities
    """

    dynamic_registration: bool
    """Execute command supports dynamic registration."""

    model_config = base_config

class SemanticTokensWorkspaceClientCapabilities(BaseModel, TypedDict):
    """
    Capabilities specific to the semantic token requests scoped to the workspace.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#semanticTokensWorkspaceClientCapabilities
    """

    refresh_support: bool
    """
    Whether the client implementation supports a refresh request sent from
    the server to the client.

    Note that this event is global and will force the client to refresh all
    semantic tokens currently shown. It should be used with absolute care
    and is useful for situation where a server for example detect a project
    wide change that requires such a calculation.
    """

    model_config = base_config

class CodeLensWorkspaceClientCapabilities(BaseModel, TypedDict):
    """
    Capabilities specific to the code lens requests scoped to the workspace.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#codeLensWorkspaceClientCapabilities
    """

    refresh_support: bool
    """
    Whether the client implementation supports a refresh request sent from the
    server to the client.

    Note that this event is global and will force the client to refresh all
    code lenses currently shown. It should be used with absolute care and is
    useful for situation where a server for example detect a project wide
    change that requires such a calculation.
    """

    model_config = base_config

class InlineValueWorkspaceClientCapabilities(BaseModel, TypedDict):
    """
    Client workspace capabilities specific to inline values.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#inlineValueWorkspaceClientCapabilities
    """

    refresh_support: bool
    """
    Whether the client implementation supports a refresh request sent from
    the server to the client.

    Note that this event is global and will force the client to refresh all
    inline values currently shown. It should be used with absolute care and
    is useful for situation where a server for example detect a project wide
    change that requires such a calculation.
    """

    model_config = base_config
