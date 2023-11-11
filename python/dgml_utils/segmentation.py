from lxml import etree
from typing import List, Optional

from dgml_utils.config import (
    DEFAULT_XML_MODE,
    DEFAULT_MIN_TEXT_LENGTH,
    DEFAULT_SUBCHUNK_TABLES,
    DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    DEFAULT_PARENT_HIERARCHY_LEVELS,
    DEFAULT_MAX_TEXT_LENGTH,
    STRUCTURE_KEY,
    TABLE_NAME,
)
from dgml_utils.conversions import (
    clean_tag,
    simplified_xml,
    text_node_to_text,
    xhtml_table_to_text,
)
from dgml_utils.locators import xpath
from dgml_utils.models import Chunk


def is_descendant_of_structural(node) -> bool:
    """True if node is a descendant of a node with the structure attribute set."""
    for ancestor in node.iterancestors():
        if STRUCTURE_KEY in ancestor.attrib:
            return True
    return False


def is_structural(node) -> bool:
    """True if node itself has the structure attribute set."""
    return node is not None and STRUCTURE_KEY in node.attrib


def has_structural_children(node) -> bool:
    """True if node has any descendents (at any depth) with the structure attribute set."""
    return len(node.findall(f".//*[@{STRUCTURE_KEY}]")) > 0


def get_chunks(
    node,
    min_text_length=DEFAULT_MIN_TEXT_LENGTH,
    max_text_length=DEFAULT_MAX_TEXT_LENGTH,
    whitespace_normalize_text=DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    sub_chunk_tables=DEFAULT_SUBCHUNK_TABLES,
    xml_mode=DEFAULT_XML_MODE,
    parent_hierarchy_levels=DEFAULT_PARENT_HIERARCHY_LEVELS,
) -> List[Chunk]:
    """Returns all structural chunks in the given node, combining small chunks with following structural nodes."""
    chunks: List[Chunk] = []
    prepended_small_chunk: Optional[Chunk] = None

    if not xml_mode and parent_hierarchy_levels > 0:
        raise Exception(
            f"Contradictory configuration: xml_mode is {xml_mode} while parent_hierarchy_levels is {parent_hierarchy_levels}. Hierarchy is only supported when including XML tags."
        )

    def build_chunk(node, table_node: bool, text_node: bool, parent_hierarchy_levels: int) -> Chunk:
        if xml_mode:
            node_text = simplified_xml(
                node,
                whitespace_normalize=whitespace_normalize_text,
                parent_hierarchy_levels=parent_hierarchy_levels,
                max_text_length=max_text_length,
            )
        elif table_node:
            node_text = xhtml_table_to_text(node, whitespace_normalize=whitespace_normalize_text)
        elif text_node:
            node_text = text_node_to_text(node, whitespace_normalize=whitespace_normalize_text)
        else:
            raise Exception("Cannot build chunk since it is not a node (table or text)")

        return Chunk(
            tag=clean_tag(node),
            text=node_text,
            xml=etree.tostring(node, encoding="unicode"),
            structure=node.attrib.get(STRUCTURE_KEY) or "",
            xpath=xpath(node),
        )

    def traverse(node):
        nonlocal prepended_small_chunk  # Access the variable from the outer scope

        is_table_leaf_node = node.tag == TABLE_NAME and not sub_chunk_tables
        is_text_leaf_node = is_structural(node) and not has_structural_children(node)
        is_structure_orphaned_node = is_descendant_of_structural(node) and not has_structural_children(node)

        if is_table_leaf_node or is_text_leaf_node or is_structure_orphaned_node:
            chunk = build_chunk(
                node,
                table_node=is_table_leaf_node,
                text_node=is_text_leaf_node or is_structure_orphaned_node,
                parent_hierarchy_levels=0,  # current node
            )
            if parent_hierarchy_levels > 0:
                chunk.parent = build_chunk(
                    node,
                    table_node=is_table_leaf_node,
                    text_node=is_text_leaf_node or is_structure_orphaned_node,
                    parent_hierarchy_levels=parent_hierarchy_levels,  # ancestor node
                )
            if prepended_small_chunk:
                chunk = prepended_small_chunk + chunk
                prepended_small_chunk = None  # clear

            if len(chunk.text) < min_text_length or node.attrib.get(STRUCTURE_KEY) == "lim":
                # Prepend small chunks or list item markers to the following chunk
                prepended_small_chunk = chunk
            else:
                chunks.append(chunk)
        else:
            # Continue deeper in the tree
            for child in node:
                traverse(child)

    traverse(node)

    # Append any remaining prepended_small_chunk that wasn't followed by a large chunk
    if prepended_small_chunk:
        chunks.append(prepended_small_chunk)

    return chunks


def get_chunks_str(
    dgml: str,
    min_text_length=DEFAULT_MIN_TEXT_LENGTH,
    max_text_length=DEFAULT_MAX_TEXT_LENGTH,
    whitespace_normalize_text=DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    sub_chunk_tables=DEFAULT_SUBCHUNK_TABLES,
    xml_mode=DEFAULT_XML_MODE,
    parent_hierarchy_levels=DEFAULT_PARENT_HIERARCHY_LEVELS,
) -> List[Chunk]:
    root = etree.fromstring(dgml)
    return get_chunks(
        node=root,
        min_text_length=min_text_length,
        whitespace_normalize_text=whitespace_normalize_text,
        sub_chunk_tables=sub_chunk_tables,
        xml_mode=xml_mode,
        parent_hierarchy_levels=parent_hierarchy_levels,
        max_text_length=max_text_length,
    )
