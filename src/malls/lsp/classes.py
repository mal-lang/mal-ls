import logging

import tree_sitter_mal as ts_mal
from tree_sitter import Language, Parser, Point, Tree

from ..ts.utils import lsp_to_tree_sitter_position
from .models import Position

MAL_LANGUAGE = Language(ts_mal.language())
PARSER = Parser(MAL_LANGUAGE)

log = logging.getLogger(__name__)


class Document:
    """
    Class to store documents in the server.
    Includes text and tree, to be easily
    edited by TreeSitter
    """

    def __init__(self, tree: Tree, text: str, uri: str):
        self.text = text  # text is in bytes
        self.tree = tree
        self.uri = uri
        self.included_files = []

    def _pos_to_byte(self, point: Point):
        line, column = point.row, point.column
        lines = self.text.split(b"\n")

        byte_offset = 0

        for i in range(line):
            byte_offset += len(lines[i]) + 1  # +1 for the newline character

        # Add the column position in the current line
        byte_offset += column

        return byte_offset

    def _change_text(self, start: Point, end: Point, new_text: str) -> (int, int):
        """
        Auxiliary method to simply edit the text corresponding to
        the document
        """
        # we need to convert from position to byte offset
        start_byte, end_byte = self._pos_to_byte(start), self._pos_to_byte(end)
        old_final_end_byte = self.tree.root_node.end_byte

        # we also need to check if the end byte is bigger than the current
        # text length
        if old_final_end_byte < end_byte:
            # replace end of file
            self.text = self.text[:start_byte] + new_text
            # therefore, the end of the file was the last changed byte
            old_end_byte = old_final_end_byte
        else:
            # otherwise, we are changing in the middle of the file
            self.text = self.text[:start_byte] + new_text + self.text[end_byte:]
            # therefore, we only replaced things
            old_end_byte = end_byte

        return (start_byte, end_byte, old_end_byte)

    def execute_changes(self, change_range: dict, text: str) -> None:
        """
        This function will process changes to files. To do this, the source
        code must be edited, TreeSitter alerted of the location of the changes
        and finally the code must be reparsed.
        """

        # start by converting the range to TreeSitter positions
        start_position_lsp = Position(
            line=change_range.start.line, character=change_range.start.character
        )
        end_position_lsp = Position(
            line=change_range.end.line, character=change_range.end.character
        )

        start_position = lsp_to_tree_sitter_position(self.text, start_position_lsp, text)
        end_position = lsp_to_tree_sitter_position(self.text, end_position_lsp, text)

        # change text
        start_byte, end_byte, old_end_byte = self._change_text(start_position, end_position, text)

        # alert Treesitter of changes
        self.tree.edit(
            start_byte,
            old_end_byte,
            end_byte,
            start_position,
            end_position if old_end_byte == end_byte else self.tree.root_node.end_point,
            end_position,
        )

        # reparse
        self.tree = PARSER.parse(self.text, self.tree)

    def change_whole_file(self, text: str) -> None:
        """
        Since we have a completely new file, we can simply replace the text and
        reparse, as this is not a change to the tree - it's a new tree
        """

        self.text = text
        self.tree = PARSER.parse(self.text)
