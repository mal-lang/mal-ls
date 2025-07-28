from ..lsp.models import Position
from tree_sitter import Point

def lsp_to_tree_sitter_position(text: str, pos: Position) -> Point:
    """
    Converts an LSP position (UTF-16 character index) to a Tree-sitter position (UTF-8 byte offset).
    """
    lsp_line, lsp_char = pos.line, pos.character
    
    lines = text.splitlines(keepends=True)
    
    # Get correct line
    line_text = lines[lsp_line]
    
    # The idea is to conver the string to UTF-16.
    # Since UTF-16 characters correspond to 2 bytes,
    # if we multiply the character position by 2
    # and then encode back to UTF-8, we effectively
    # cut back to the byte number

    # Convert to UTF-16 (each UTF-16 code unit is 2 bytes)
    # https://en.wikipedia.org/wiki/UTF-16#Byte-order_encoding_schemes
    line_utf16 = line_text.encode('utf-16')

    # check for BOM
    bom_size = 0
    if line_utf16.startswith(b'\xff\xfe') or line_utf16.startswith(b'\xfe\xff'):
        bom_size = 2
    
    # lsp_char * 2 gives us the byte offset in the UTF-16 string
    # UTF-16 chars are 2 bytes long
    # We need to take into account possible BOM
    #
    # lsp_char refers to the position according to the source encoding,
    # decided by the server and client. For now, it is only UTF-16
    utf16_slice = line_utf16[bom_size:bom_size + lsp_char * 2]
    
    # return to unicode
    string_slice = utf16_slice.decode('utf-16')
    
    # Encode the string slice to UTF-8 and get its byte length
    byte_offset = len(string_slice.encode('utf-8'))
    
    return Point(lsp_line, byte_offset)
