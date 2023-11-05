from lxml import etree
from typing import List

from .models import Chunk

STRUCTURE_KEY = "structure"


def is_structural(element) -> bool:
    """True if element itself has the structure attribute set."""
    return element is not None and STRUCTURE_KEY in element.attrib


def has_structural_children(element) -> bool:
    """True if element has any children with the structure attribute set."""
    return len(element.findall(f"./*[@{STRUCTURE_KEY}]")) > 0


def get_leaf_structural_chunks(element) -> List[Chunk]:
    """Returns all leaf structural nodes in the given element."""
    leaf_chunks = []

    def traverse(node):
        if is_structural(node) and not has_structural_children(node):
            # Found a leaf structural node
            leaf_chunks.append(
                Chunk(
                    tag=node.tag,
                    text=" ".join(node.itertext()).strip(),
                    xml=etree.tostring(node, encoding="unicode"),
                    structure=node.attrib.get(STRUCTURE_KEY),
                )
            )
        else:
            # Continue deeper in the tree
            for child in node:
                traverse(child)

    traverse(element)
    return leaf_chunks


def get_leaf_structural_chunks_str(dgml: str) -> List[Chunk]:
    root = etree.fromstring(dgml)
    return get_leaf_structural_chunks(root)
