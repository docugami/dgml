from lxml import etree
from typing import List, Optional

from dgml.config import (
    DEFAULT_MIN_CHUNK_SIZE,
    DEFAULT_SUBCHUNK_TABLES,
    DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    STRUCTURE_KEY,
    TABLE_NAME,
)
from dgml.conversions import text_node_to_text, xhtml_table_to_text
from dgml.models import Chunk


def is_structural(element) -> bool:
    """True if element itself has the structure attribute set."""
    return element is not None and STRUCTURE_KEY in element.attrib


def has_structural_children(element) -> bool:
    """True if element has any children with the structure attribute set."""
    return len(element.findall(f"./*[@{STRUCTURE_KEY}]")) > 0


def get_leaf_structural_chunks(
    element,
    min_chunk_size=DEFAULT_MIN_CHUNK_SIZE,
    whitespace_normalize_text=DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    sub_chunk_tables=DEFAULT_SUBCHUNK_TABLES,
) -> List[Chunk]:
    """Returns all leaf structural nodes in the given element, combining small chunks with following siblings."""
    leaf_chunks: List[Chunk] = []
    prepended_small_chunk: Optional[Chunk] = None

    def traverse(node):
        nonlocal prepended_small_chunk  # Access the variable from the outer scope

        table_leaf_node = node.tag == TABLE_NAME and not sub_chunk_tables
        text_leaf_node = is_structural(node) and not has_structural_children(node)

        if table_leaf_node or text_leaf_node:
            node_text = ""
            if table_leaf_node:
                node_text = xhtml_table_to_text(node)
            elif text_leaf_node:
                node_text = text_node_to_text(node, whitespace_normalize=whitespace_normalize_text)

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


def get_leaf_structural_chunks_str(
    dgml: str,
    min_chunk_size=DEFAULT_MIN_CHUNK_SIZE,
    whitespace_normalize_text=DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    sub_chunk_tables=DEFAULT_SUBCHUNK_TABLES,
) -> List[Chunk]:
    root = etree.fromstring(dgml)
    return get_leaf_structural_chunks(
        element=root,
        min_chunk_size=min_chunk_size,
        whitespace_normalize_text=whitespace_normalize_text,
        sub_chunk_tables=sub_chunk_tables,
    )
