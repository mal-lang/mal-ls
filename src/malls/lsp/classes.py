from tree_sitter import Tree
class Document:
    """
    Class to store documents in the server.
    Includes text and tree, to be easily
    edited by TreeSitter
    """
    def __init__(self, tree: Tree, text: str):
        self.text = text # text is in bytes
        self.tree = tree
