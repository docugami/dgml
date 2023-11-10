from lxml import etree
from typing import List, Optional

from dgml_utils.config import (
    DEFAULT_INCLUDE_XML_TAGS,
    DEFAULT_MIN_CHUNK_LENGTH,
    DEFAULT_SUBCHUNK_TABLES,
    DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    DEFAULT_XML_HIERARCHY_LEVELS,
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


def is_descendant_of_structural(element) -> bool:
    """True if element is a descendant of a node with the structure attribute set."""
    for ancestor in element.iterancestors():
        if STRUCTURE_KEY in ancestor.attrib:
            return True
    return False


def is_structural(element) -> bool:
    """True if element itself has the structure attribute set."""
    return element is not None and STRUCTURE_KEY in element.attrib


def has_structural_children(element) -> bool:
    """True if element has any descendents (at any depth) with the structure attribute set."""
    return len(element.findall(f".//*[@{STRUCTURE_KEY}]")) > 0


def get_leaf_structural_chunks(
    element,
    min_chunk_length=DEFAULT_MIN_CHUNK_LENGTH,
    whitespace_normalize_text=DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    sub_chunk_tables=DEFAULT_SUBCHUNK_TABLES,
    include_xml_tags=DEFAULT_INCLUDE_XML_TAGS,
    xml_hierarchy_levels=DEFAULT_XML_HIERARCHY_LEVELS,
    max_text_length=DEFAULT_MAX_TEXT_LENGTH,
) -> List[Chunk]:
    """Returns all leaf structural nodes in the given element, combining small chunks with following structural nodes."""
    leaf_chunks: List[Chunk] = []
    prepended_small_chunk: Optional[Chunk] = None

    if not include_xml_tags and xml_hierarchy_levels > 0:
        raise Exception(
            f"Contradictory configuration: include_xml_tags is {include_xml_tags} while xml_hierarchy_levels is {xml_hierarchy_levels}. Hierarchy is only supported when including XML tags."
        )

    def build_chunk(node, table_node: bool, text_node: bool, xml_hierarchy_levels: int) -> Chunk:
        if include_xml_tags:
            node_text = simplified_xml(
                node,
                whitespace_normalize=whitespace_normalize_text,
                xml_hierarchy_levels=xml_hierarchy_levels,
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

        table_leaf_node = node.tag == TABLE_NAME and not sub_chunk_tables
        text_leaf_node = is_structural(node) and not has_structural_children(node)
        is_structure_orphaned_node = is_descendant_of_structural(node) and not has_structural_children(node)

        if table_leaf_node or text_leaf_node or is_structure_orphaned_node:
            chunk = build_chunk(
                node,
                table_node=table_leaf_node,
                text_node=text_leaf_node or is_structure_orphaned_node,
                xml_hierarchy_levels=0,  # current node
            )
            if xml_hierarchy_levels > 0:
                chunk.parent = build_chunk(
                    node,
                    table_node=table_leaf_node,
                    text_node=text_leaf_node or is_structure_orphaned_node,
                    xml_hierarchy_levels=xml_hierarchy_levels,  # ancestor node
                )
            if prepended_small_chunk:
                chunk = prepended_small_chunk + chunk
                prepended_small_chunk = None  # clear

            if len(chunk.text) < min_chunk_length or node.attrib.get(STRUCTURE_KEY) == "lim":
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
    min_chunk_length=DEFAULT_MIN_CHUNK_LENGTH,
    whitespace_normalize_text=DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    sub_chunk_tables=DEFAULT_SUBCHUNK_TABLES,
    include_xml_tags=DEFAULT_INCLUDE_XML_TAGS,
    xml_hierarchy_levels=DEFAULT_XML_HIERARCHY_LEVELS,
    max_text_length=DEFAULT_MAX_TEXT_LENGTH,
) -> List[Chunk]:
    root = etree.fromstring(dgml)
    return get_leaf_structural_chunks(
        element=root,
        min_chunk_length=min_chunk_length,
        whitespace_normalize_text=whitespace_normalize_text,
        sub_chunk_tables=sub_chunk_tables,
        include_xml_tags=include_xml_tags,
        xml_hierarchy_levels=xml_hierarchy_levels,
        max_text_length=max_text_length,
    )
