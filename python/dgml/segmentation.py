from lxml import etree
from typing import List, Optional

from .models import Chunk

STRUCTURE_KEY = "structure"
DEFAULT_MIN_CHUNK_SIZE = 8  # Default length threshold for determining small chunks


def is_structural(element) -> bool:
    """True if element itself has the structure attribute set."""
    return element is not None and STRUCTURE_KEY in element.attrib


def has_structural_children(element) -> bool:
    """True if element has any children with the structure attribute set."""
    return len(element.findall(f"./*[@{STRUCTURE_KEY}]")) > 0


def get_leaf_structural_chunks(
    element,
    min_chunk_size=DEFAULT_MIN_CHUNK_SIZE,
    whitespace_normalize_text=True,
) -> List[Chunk]:
    """Returns all leaf structural nodes in the given element, combining small chunks with following siblings."""
    leaf_chunks: List[Chunk] = []
    prepended_small_chunk: Optional[Chunk] = None

    def traverse(node):
        nonlocal prepended_small_chunk  # Access the variable from the outer scope
        if is_structural(node) and not has_structural_children(node):
            node_text = " ".join(node.itertext()).strip()
            if whitespace_normalize_text:
                node_text = " ".join(node_text.split()).strip()
            chunk = Chunk(
                tag=node.tag,
                text=node_text,
                xml=etree.tostring(node, encoding="unicode"),
                structure=node.attrib.get(STRUCTURE_KEY),
            )
            if prepended_small_chunk:
                chunk = prepended_small_chunk + chunk
                prepended_small_chunk = None  # clear

            if len(chunk.text) < min_chunk_size or node.attrib.get(STRUCTURE_KEY) == "lim":
                # Prepend small chunks or list item markers to the following chunk
                prepended_small_chunk = chunk
            else:
                leaf_chunks.append(chunk)
        else:
            # Continue deeper in the tree
            for child in node:
                traverse(child)

    traverse(element)

    # Append any remaining prepended_small_chunk that wasn't followed by a large chunk
    if prepended_small_chunk:
        leaf_chunks.append(prepended_small_chunk)

    return leaf_chunks


def get_leaf_structural_chunks_str(dgml: str) -> List[Chunk]:
    root = etree.fromstring(dgml)
    return get_leaf_structural_chunks(root)
