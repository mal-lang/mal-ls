from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_snake
from typing_extensions import TypedDict
from uritools import isuri

from .enums import DiagnosticSeverity, DiagnosticTag, MarkupKind

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

    severity: DiagnosticSeverity | None
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

    tags: list[DiagnosticTag] | None
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

    kind: MarkupKind
    """
    The type of the Markup
    """

    value: str
    """
    The content itself
    """
