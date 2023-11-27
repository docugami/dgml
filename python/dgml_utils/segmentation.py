from copy import deepcopy
from lxml import etree
from typing import List, Optional

from dgml_utils.config import (
    DEFAULT_HIERARCHY_MODE,
    DEFAULT_INCLUDE_XML_TAGS,
    DEFAULT_MIN_TEXT_LENGTH,
    DEFAULT_SUBCHUNK_TABLES,
    DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    DEFAULT_PARENT_HIERARCHY_LEVELS,
    DEFAULT_MAX_TEXT_LENGTH,
    STRUCTURE_KEY,
    STYLE_KEY,
    TABLE_NAME,
    HierarchyMode,
)
from dgml_utils.conversions import (
    clean_tag,
    simplified_xml,
    text_node_to_text,
    xhtml_table_to_text,
    xml_nth_ancestor,
)
from dgml_utils.locators import xpath
from dgml_utils.models import BoundingBox, Chunk


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


def is_force_prepend_chunk(node) -> bool:
    return node is not None and node.attrib.get(STRUCTURE_KEY) in ["lim"]


def get_chunks(
    node,
    min_text_length=DEFAULT_MIN_TEXT_LENGTH,
    max_text_length=DEFAULT_MAX_TEXT_LENGTH,
    whitespace_normalize_text=DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    sub_chunk_tables=DEFAULT_SUBCHUNK_TABLES,
    include_xml_tags=DEFAULT_INCLUDE_XML_TAGS,
    parent_hierarchy_levels=DEFAULT_PARENT_HIERARCHY_LEVELS,
    hierarchy_mode=DEFAULT_HIERARCHY_MODE,
) -> List[Chunk]:
    """Returns all structural chunks in the given node, as xml chunks."""
    final_chunks: List[Chunk] = []
    prepended_chunk: Optional[Chunk] = None

    def _build_chunks(
        node,
        include_xml_tags=DEFAULT_INCLUDE_XML_TAGS,
        max_text_length=DEFAULT_MAX_TEXT_LENGTH,
        whitespace_normalize_text=DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    ) -> List[Chunk]:
        """
        Builds chunks from the given node, splitting on the given max length to ensure
        all the returned chunks as less than the given max length.
        """
        if include_xml_tags:
            node_text = simplified_xml(
                node,
                whitespace_normalize_text=whitespace_normalize_text,
            )
        elif node.tag == TABLE_NAME:
            node_text = xhtml_table_to_text(node, whitespace_normalize=whitespace_normalize_text)
        else:
            node_text = text_node_to_text(node, whitespace_normalize=whitespace_normalize_text)

        node_text_splits = [node_text[i : i + max_text_length] for i in range(0, len(node_text), max_text_length)]

        chunks = []
        for text in node_text_splits:
            chunks.append(
                Chunk(
                    tag=clean_tag(node),
                    text=text,
                    xml=etree.tostring(node, encoding="unicode"),
                    structure=(node.attrib.get(STRUCTURE_KEY) or "").strip(),
                    xpath=xpath(node),
                    bboxes=BoundingBox.from_style(node.attrib.get(STYLE_KEY)),
                )
            )
        return chunks

    def _traverse(node):
        nonlocal prepended_chunk  # Access the variable from the outer scope

        is_table_leaf_node = node.tag == TABLE_NAME and not sub_chunk_tables
        is_text_leaf_node = is_structural(node) and not has_structural_children(node)
        is_structure_orphaned_node = is_descendant_of_structural(node) and not has_structural_children(node)

        if is_table_leaf_node or is_text_leaf_node or is_structure_orphaned_node:
            sub_chunks: List[Chunk] = _build_chunks(
                node,
                include_xml_tags=include_xml_tags,
                max_text_length=max_text_length,
                whitespace_normalize_text=whitespace_normalize_text,
            )
            ancestor_chunk = None
            if hierarchy_mode == HierarchyMode.Structure and parent_hierarchy_levels > 0:
                # Try to use tree hierarchy directly from the node in structure hierarchy
                # mode. For window hierarchy mode, we do this below once all chunks are
                # calculated, so no parent set here.
                semantic_ancestor_node = xml_nth_ancestor(
                    node,
                    n=parent_hierarchy_levels,
                    max_text_length=max_text_length,
                    whitespace_normalize_text=whitespace_normalize_text,
                )
                structural_ancestor_node = xml_nth_ancestor(
                    node,
                    n=parent_hierarchy_levels,
                    max_text_length=max_text_length,
                    whitespace_normalize_text=whitespace_normalize_text,
                    skip_tags=None,  # don't skip anything
                )

                # We split the current chunk into sub-chunks if longer than max length,
                # to avoid loss of text. However, if the ancestor is longer than max length
                # what do we do? For now let's just pick the first ancestor (larger of)
                # semantic or non-semantic but this could be lossy.
                semantic_ancestor_chunk = _build_chunks(
                    semantic_ancestor_node,
                    include_xml_tags=include_xml_tags,
                    max_text_length=max_text_length,
                    whitespace_normalize_text=whitespace_normalize_text,
                )[0]
                structural_ancestor_chunk = _build_chunks(
                    structural_ancestor_node,
                    include_xml_tags=include_xml_tags,
                    max_text_length=max_text_length,
                    whitespace_normalize_text=whitespace_normalize_text,
                )[0]
                if len(semantic_ancestor_chunk.text) > len(structural_ancestor_chunk.text):
                    # Prefer the semantic ancestor if it is larger (normal case)
                    ancestor_chunk = semantic_ancestor_chunk
                else:
                    # If we can get more context with a structural ancestor, take that instead
                    ancestor_chunk = structural_ancestor_chunk

            for chunk in sub_chunks:
                if prepended_chunk:
                    chunk = prepended_chunk + chunk
                    prepended_chunk = None  # clear

                if is_force_prepend_chunk(node):
                    # Prepend list item markers and other force prepend chunks to the following chunk
                    # without any trailing whitespace
                    prepended_chunk = chunk
                elif len(chunk.text) < min_text_length:
                    # If chunk is less than min length, prepend with a line break
                    chunk.text += "\n"
                    prepended_chunk = chunk
                else:
                    if ancestor_chunk:
                        # If an ancestor chunk is set, we always want it to be bigger than the current
                        # chunk, yet sometimes due to prepended chunks, skip tags and length limits you
                        # can get situations where the ancestor chunk found in the tree ends up being smaller
                        # than the (perhaps concatenated and built up) current chunk. Fix that case here.
                        if len(ancestor_chunk.text) > len(chunk.text):
                            chunk.parent = ancestor_chunk
                        else:
                            # self-parent
                            chunk.parent = chunk

                    final_chunks.append(chunk)
        else:
            # Continue deeper in the tree
            for child in node:
                _traverse(child)

    _traverse(node)

    # Append any remaining prepended_small_chunk that wasn't followed by a large chunk
    if prepended_chunk:
        final_chunks.append(prepended_chunk)

    if hierarchy_mode == HierarchyMode.Window and parent_hierarchy_levels > 0:
        # Set parents for text chunks using flat window of before/after chunks
        for i, current_chunk in enumerate(final_chunks):
            parent_chunk_range_start = max(0, i - parent_hierarchy_levels)
            parent_chunk_range_end = min(len(final_chunks), i + parent_hierarchy_levels + 1)
            parent_chunks = final_chunks[parent_chunk_range_start:parent_chunk_range_end]
            for pc in parent_chunks:
                if not current_chunk.parent:
                    current_chunk.parent = pc
                else:
                    parent_clone = deepcopy(current_chunk.parent)
                    current_chunk.parent = parent_clone + pc
                    # Instead of default text add behaviour, add a newline
                    current_chunk.parent.text = parent_clone.text + "\n" + pc.text
    return final_chunks


def get_chunks_str(
    dgml: str,
    min_text_length=DEFAULT_MIN_TEXT_LENGTH,
    max_text_length=DEFAULT_MAX_TEXT_LENGTH,
    whitespace_normalize_text=DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    sub_chunk_tables=DEFAULT_SUBCHUNK_TABLES,
    include_xml_tags=DEFAULT_INCLUDE_XML_TAGS,
    parent_hierarchy_levels=DEFAULT_PARENT_HIERARCHY_LEVELS,
    hierarchy_mode=DEFAULT_HIERARCHY_MODE,
) -> List[Chunk]:
    root = etree.fromstring(dgml)

    return get_chunks(
        node=root,
        min_text_length=min_text_length,
        max_text_length=max_text_length,
        whitespace_normalize_text=whitespace_normalize_text,
        sub_chunk_tables=sub_chunk_tables,
        include_xml_tags=include_xml_tags,
        parent_hierarchy_levels=parent_hierarchy_levels,
        hierarchy_mode=hierarchy_mode,
    )
