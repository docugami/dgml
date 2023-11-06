from lxml import etree
from tabulate import tabulate

from dgml_utils.config import DEFAULT_TABLE_FORMAT_AS_TEXT, DEFAULT_WHITESPACE_NORMALIZE_TEXT, NAMESPACES, TABLE_NAME


def text_node_to_text(node, whitespace_normalize=DEFAULT_WHITESPACE_NORMALIZE_TEXT) -> str:
    node_text = " ".join(node.itertext())
    if whitespace_normalize:
        node_text = " ".join(node_text.split()).strip()
    return node_text


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


def simplified_xml(node, whitespace_normalize=DEFAULT_WHITESPACE_NORMALIZE_TEXT) -> str:
    """Renders given node to simplified XML without attributes or namespaces."""
    if node is None:
        return ""

    # Recursive function to copy over elements to a new tree without
    # namespaces and attributes
    def strip_ns_and_attribs(element):
        # Create a new element without namespace or attributes
        stripped_el = etree.Element(etree.QName(element).localname)
        # Copy text and tail (if any)
        stripped_el.text = element.text
        stripped_el.tail = element.tail
        # Recursively apply this function to all children
        for child in element:
            stripped_el.append(strip_ns_and_attribs(child))
        return stripped_el

    simplified_node = strip_ns_and_attribs(node)
    xml = etree.tostring(simplified_node, encoding="unicode")

    # remove empty non-semantic chunks from output
    xml = xml.replace("<chunk>", "").replace("</chunk>", "")
    if whitespace_normalize:
        xml = " ".join(xml.split()).strip()
    return xml.strip()
