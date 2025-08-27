import pytest

from malls.lsp.models import Position
from malls.ts.utils import lsp_to_tree_sitter_position, tree_sitter_to_lsp_position

# (text, input/utf16/lsp position, output/utf8/ts position)
parameters = [
    # h e l l o   w o r l d
    # 0 1 2 3 4 5 6 7 8 9 10
    # target 'w' - position 6
    ("hello world".encode(), (0, 6), (0, 6)),
    # emoji takes 2 UTF-16 characters, so the emoji is 4 bytes
    # a  🚀   b
    # 0  1 2  3
    # target 'b' - 3
    # In bytes should be 5, 1 for 'a', 4 for emoji
    ("a🚀b".encode(), (0, 3), (0, 5)),
    # ß ç  🐍
    # 0 1  2 3
    # target '🐍' - position 2 (start)
    # In bytes ß, ç take 2 bytes and emoji 4 -> position 2+2 = 4
    ("ßç🐍".encode(), (0, 2), (0, 4)),
    (" ".encode(), (0, 0), (0, 0)),
]
parameter_ids = ["ascii_chars_only", "with_emoji", "ascii_and_multibyte_chars", "empty_string"]


@pytest.mark.parametrize("text,lsp_position,ts_position", parameters, ids=parameter_ids)
def test_position_conversion(text: bytes, lsp_position: (int, int), ts_position: (int, int)):
    position = Position(line=lsp_position[0], character=lsp_position[1])

    result_position = lsp_to_tree_sitter_position(text, position)
    assert result_position == ts_position
    assert tree_sitter_to_lsp_position(text, result_position) == position
