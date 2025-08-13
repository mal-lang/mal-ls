from malls.lsp.models import Position
from malls.ts.utils import lsp_to_tree_sitter_position, tree_sitter_to_lsp_position


def test_ascii_chars_only():
    text = b"hello world"

    # h e l l o   w o r l d
    # 0 1 2 3 4 5 6 7 8 9 10
    # target 'w' - position 6

    position = Position(line=0, character=6)

    result_position = lsp_to_tree_sitter_position(text, position)
    assert result_position == (0, 6)
    assert tree_sitter_to_lsp_position(text, result_position) == position


def test_with_emoji():
    text = "a🚀b".encode()  # emoji takes 2 UTF-16 characters, so the emoji is 4 bytes

    # a  🚀   b
    # 0  1 2  3
    # target 'b' - 3

    position = Position(line=0, character=3)

    # In bytes should be 5, 1 for 'a', 4 for emoji

    result_position = lsp_to_tree_sitter_position(text, position)
    assert result_position == (0, 5)
    assert tree_sitter_to_lsp_position(text, result_position) == position


def test_ascii_and_multibyte_chars():
    text = "ßç🐍".encode()

    # ß ç  🐍
    # 0 1  2 3
    # target '🐍' - position 2 (start)

    position = Position(line=0, character=2)

    # In bytes ß, ç take 2 bytes and emoji 4 -> position 2+2 = 4

    result_position = lsp_to_tree_sitter_position(text, position)
    assert result_position == (0, 4)
    assert tree_sitter_to_lsp_position(text, result_position) == position


def test_empty_string():
    text = b" "

    position = Position(line=0, character=0)

    result_position = lsp_to_tree_sitter_position(text, position)
    assert result_position == (0, 0)
    assert tree_sitter_to_lsp_position(text, result_position) == position
