from lxml import etree
from tabulate import tabulate

from dgml_utils.config import (
    DEFAULT_XML_HIERARCHY_LEVELS,
    DEFAULT_SKIP_XML_TAGS,
    DEFAULT_TABLE_FORMAT_AS_TEXT,
    DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    DEFAULT_MAX_TEXT_SIZE,
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
    skip_tags=DEFAULT_SKIP_XML_TAGS,
    max_text_size=DEFAULT_MAX_TEXT_SIZE,
    whitespace_normalize=DEFAULT_WHITESPACE_NORMALIZE_TEXT,
):
    """
    Finds the nth ancestor of a given lxml node, skipping nodes with tags in skip_tags and considering text size limit.

    :param node: The lxml node from which to find the ancestor
    :param n: The number of ancestors to go up the XML tree. If n <= 0, the node itself is returned.
    :param skip_tags: Tags to skip when counting ancestors
    :param max_text_size: The maximum size of text allowed before stopping the search
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
            filtered_ancestors = [anc for anc in all_ancestors if clean_tag(anc) not in skip_tags]

            for i, ancestor in enumerate(filtered_ancestors):
                if len(text_node_to_text(ancestor, whitespace_normalize)) > max_text_size or i + 1 == n:
                    return ancestor

    # If no ancestors are found, return the node itself
    return filtered_ancestors[-1] if filtered_ancestors else node


def simplified_element(node):
    """
    Recursive function to copy over elements to a new tree without namespaces and attributes.

    :param node: lxml node to simplify
    :return: Simplified lxml element

    >>> root = etree.XML('<root xmlns="http://test.com" attr="value"><child>Text</child></root>')
    >>> print(etree.tostring(simplified_element(root), encoding='unicode'))
    <root><child>Text</child></root>
    """

    # Create a new element without namespace or attributes
    stripped_el = etree.Element(etree.QName(node).localname)
    # Copy text and tail (if any)
    stripped_el.text = node.text
    stripped_el.tail = node.tail
    # Recursively apply this function to all children
    for child in node:
        stripped_el.append(simplified_element(child))
    return stripped_el


def simplified_xml(
    node,
    whitespace_normalize=DEFAULT_WHITESPACE_NORMALIZE_TEXT,
    skip_tags=DEFAULT_SKIP_XML_TAGS,
    xml_hierarchy_levels=DEFAULT_XML_HIERARCHY_LEVELS,
    max_text_size=DEFAULT_MAX_TEXT_SIZE,
) -> str:
    """
    Renders the given node (or parent at specified hierarchy level) to simplified XML
    without attributes or namespaces.

    :param node: The lxml node to simplify
    :param whitespace_normalize: Whether to normalize whitespace in text node processing
    :param skip_tags: Tags to skip when counting ancestors
    :param xml_hierarchy_levels: The number of hierarchy levels to go up from the node
    :param max_text_size: The maximum size of chunk returned (by text)
    :return: Simplified XML string

    >>> nsmap = {'ns': 'http://test.com'}
    >>> root = etree.XML('<root xmlns="http://test.com"><parent attr="ignore"><skip><child>Text</child></skip></parent></root>')
    >>> child = root.find('.//ns:child', namespaces=nsmap)
    >>> print(simplified_xml(child, skip_tags=['skip'], xml_hierarchy_levels=100))
    <root><parent><child>Text</child></parent></root>
    >>> print(simplified_xml(child, skip_tags=['skip'], xml_hierarchy_levels=100, max_text_size=9))
    <root><pa
    """
    if node is None:
        return ""

    node = nth_ancestor(
        node,
        n=xml_hierarchy_levels,
        skip_tags=skip_tags,
        max_text_size=max_text_size,
        whitespace_normalize=whitespace_normalize,
    )
    simplified_node = simplified_element(node)

    xml = etree.tostring(simplified_node, encoding="unicode")

    # remove skip tags from output
    for skip_tag in skip_tags:
        xml = xml.replace(f"<{skip_tag}>", "").replace(f"</{skip_tag}>", "")

    if whitespace_normalize:
        xml = " ".join(xml.split()).strip()
    return xml.strip()[:max_text_size].strip()
