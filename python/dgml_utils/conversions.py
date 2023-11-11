from lxml import etree
from tabulate import tabulate

from dgml_utils.config import (
    DEFAULT_PARENT_HIERARCHY_LEVELS,
    DEFAULT_SKIP_TAGS,
    DEFAULT_TABLE_FORMAT_AS_TEXT,
    DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    DEFAULT_MAX_TEXT_LENGTH,
    NAMESPACES,
    TABLE_NAME,
)


def text_node_to_text(node, whitespace_normalize=DEFAULT_WHITESPACE_NORMALIZE_TEXT) -> str:
    """
    Extracts and normalizes all text within an XML node.

    :param node: lxml node from which to extract text
    :param whitespace_normalize: flag to normalize whitespace
    :return: Normalized text string of all text within the node

    >>> root = etree.XML("<root> Hello  <child>World!</child></root>")
    >>> text_node_to_text(root)
    'Hello World!'
    >>> root = etree.XML("<root>  Hello   \\n\\nWorld!  </root>")
    >>> text_node_to_text(root)
    'Hello World!'
    >>> text_node_to_text(root, whitespace_normalize=False)
    '  Hello   \\n\\nWorld!  '
    """
    node_text = " ".join(node.itertext())
    if whitespace_normalize:
        node_text = " ".join(node_text.split()).strip()
    return node_text


def clean_tag(node) -> str:
    """
    Returns the clean (no namespace) tag for an lxml node.

    :param node: lxml node for which to get the clean tag
    :return: Clean tag as a string

    >>> node = etree.Element('{namespace}tag')
    >>> clean_tag(node)
    'tag'
    """
    if node is None:
        return ""
    return etree.QName(node).localname


def xhtml_table_to_text(
    node,
    whitespace_normalize=DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    format=DEFAULT_TABLE_FORMAT_AS_TEXT,
) -> str:
    """Converts HTML table to formatted text."""
    if node.tag != TABLE_NAME:
        raise Exception("Please provide an XHTML table node for conversion.")

    rows = []
    for tr in node.xpath(".//xhtml:tr", namespaces=NAMESPACES):
        cells = [
            text_node_to_text(td_node, whitespace_normalize=whitespace_normalize)
            for td_node in tr.xpath(".//xhtml:td", namespaces=NAMESPACES)
        ]
        rows.append(cells)

    return tabulate(rows, tablefmt=format)


def nth_ancestor(
    node,
    n: int,
    skip_tags=DEFAULT_SKIP_TAGS,
    max_text_length=DEFAULT_MAX_TEXT_LENGTH,
    whitespace_normalize=DEFAULT_WHITESPACE_NORMALIZE_TEXT,
):
    """
    Finds the nth ancestor of a given lxml node, skipping nodes with tags in skip_tags and considering text length limit.

    :param node: The lxml node from which to find the ancestor
    :param n: The number of ancestors to go up the XML tree. If n <= 0, the node itself is returned.
    :param skip_tags: Tags to skip when counting ancestors
    :param max_text_length: The maximum length of text allowed before stopping the search
    :param whitespace_normalize: Whether to normalize whitespace in text node processing
    :return: The nth ancestor lxml node or the node itself if n <= 0 or no ancestors are found

    >>> root = etree.XML("<root><parent><skip><child>Some text</child></skip></parent></root>")
    >>> child = root.find('.//child')
    >>> ancestor = nth_ancestor(child, 1, skip_tags=['skip'])
    >>> clean_tag(ancestor)
    'parent'
    >>> ancestor = nth_ancestor(child, 0)
    >>> clean_tag(ancestor)
    'child'
    >>> ancestor = nth_ancestor(child, -1)
    >>> clean_tag(ancestor)
    'child'
    >>> ancestor = nth_ancestor(child, 2, skip_tags=['skip'])
    >>> clean_tag(ancestor)
    'root'
    >>> orphan = etree.XML("<orphan>No parents</orphan>")
    >>> ancestor = nth_ancestor(orphan, 1)
    >>> clean_tag(ancestor)
    'orphan'
    """
    if n <= 0 or node is None:
        return node

    filtered_ancestors = []
    if node is not None:
        all_ancestors = [anc for anc in node.xpath("ancestor::*")]
        all_ancestors.reverse()  # start from parent up, not root down
        if all_ancestors:
            for anc in all_ancestors:
                if clean_tag(anc) in skip_tags:
                    continue
                ancestor_text_length = len(simplified_xml(anc, whitespace_normalize, parent_hierarchy_levels=0))
                if ancestor_text_length <= max_text_length:
                    node = anc
                    filtered_ancestors.append(anc)
                else:
                    break  # Stop walking ancestor chain if max text length is exceeded

            for i, ancestor in enumerate(filtered_ancestors):
                if i + 1 == n:
                    return ancestor

    return node


def simplified_node(node):
    """
    Recursive function to copy over nodes to a new tree without namespaces and attributes.

    :param node: lxml node to simplify
    :return: Simplified lxml node

    >>> root = etree.XML('<root xmlns="http://test.com" attr="value"><child>Text</child></root>')
    >>> print(etree.tostring(simplified_node(root), encoding='unicode'))
    <root><child>Text</child></root>
    """

    # Create a new node without namespace or attributes
    stripped_el = etree.Element(etree.QName(node).localname)
    # Copy text and tail (if any)
    stripped_el.text = node.text
    stripped_el.tail = node.tail
    # Recursively apply this function to all children
    for child in node:
        stripped_el.append(simplified_node(child))
    return stripped_el


def simplified_xml(
    node,
    whitespace_normalize=DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    skip_tags=DEFAULT_SKIP_TAGS,
    parent_hierarchy_levels=DEFAULT_PARENT_HIERARCHY_LEVELS,
    max_text_length=DEFAULT_MAX_TEXT_LENGTH,
) -> str:
    """
    Renders the given node (or parent at specified hierarchy level) to simplified XML
    without attributes or namespaces.

    :param node: The lxml node to simplify
    :param whitespace_normalize: Whether to normalize whitespace in text node processing
    :param skip_tags: Tags to skip when counting ancestors
    :param parent_hierarchy_levels: The number of hierarchy levels to go up from the node
    :param max_text_length: The maximum length of chunk returned (by text)
    :return: Simplified XML string

    >>> nsmap = {'ns': 'http://test.com'}
    >>> root = etree.XML('<root xmlns="http://test.com"><parent><skip><child>Text</child><sibling attr="test">foo</sibling></skip></parent>Mixed text very long</root>')
    >>> child = root.find('.//ns:child', namespaces=nsmap)

    # Test walking up hierarchy level without skipping or max text length
    # >>> print(simplified_xml(child, parent_hierarchy_levels=1))
    # <skip><child>Text</child><sibling>foo</sibling></skip>

    Test walking up hierarchy level with skipping but no max text length
    >>> print(simplified_xml(child, skip_tags=['skip'], parent_hierarchy_levels=1))
    <parent><child>Text</child><sibling>foo</sibling></parent>Mixed text very long

    Test walking up hierarchy level with skipping but stopping at the root
    >>> print(simplified_xml(child, skip_tags=['skip'], parent_hierarchy_levels=100))
    <root><parent><child>Text</child><sibling>foo</sibling></parent>Mixed text very long</root>

    Test walking up hierarchy level with skipping but early stopping due to max text length
    >>> print(simplified_xml(child, skip_tags=['skip'], parent_hierarchy_levels=100, max_text_length=40))
    <child>Text</child>

    Test forced truncation of current node if it is large
    >>> print(simplified_xml(child, max_text_length=9))
    <child>Te
    """
    if node is None:
        return ""

    node = nth_ancestor(
        node,
        n=parent_hierarchy_levels,
        skip_tags=skip_tags,
        max_text_length=max_text_length,
        whitespace_normalize=whitespace_normalize,
    )

    simplified_xml = etree.tostring(simplified_node(node), encoding="unicode")

    # remove skip tags from output
    for skip_tag in skip_tags:
        simplified_xml = simplified_xml.replace(f"<{skip_tag}>", "").replace(f"</{skip_tag}>", "")

    if whitespace_normalize:
        simplified_xml = " ".join(simplified_xml.split()).strip()
    return simplified_xml.strip()[:max_text_length].strip()
