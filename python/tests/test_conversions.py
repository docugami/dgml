import pytest
from lxml import etree
from dgml.config import NAMESPACES

from dgml.conversions import text_node_to_text, xhtml_table_to_text


def test_text_node_to_text():
    element = etree.Element("root")
    element.text = "  Hello   \n\nWorld  "
    assert text_node_to_text(element) == "Hello World"
    assert text_node_to_text(element, whitespace_normalize=False) == "  Hello   \n\nWorld  "


def test_xhtml_table_to_text():
    xhtml_data = """
    <xhtml:table xmlns:xhtml="http://www.w3.org/1999/xhtml">
        <xhtml:tbody>
            <xhtml:tr>
                <xhtml:td>Item</xhtml:td>
                <xhtml:td>Quantity</xhtml:td>
            </xhtml:tr>
            <xhtml:tr>
                <xhtml:td>Apples</xhtml:td>
                <xhtml:td>10</xhtml:td>
            </xhtml:tr>
            <xhtml:tr>
                <xhtml:td>Bananas</xhtml:td>
                <xhtml:td>5</xhtml:td>
            </xhtml:tr>
        </xhtml:tbody>
    </xhtml:table>
    """

    # Parse the mock XHTML table string
    table_node = etree.fromstring(xhtml_data)

    # Expected formatted table output using the 'grid' format (may need adjustment to match the actual expected output)
    expected_table = (
        "+---------+----------+\n"
        "| Item    | Quantity |\n"
        "+---------+----------+\n"
        "| Apples  | 10       |\n"
        "+---------+----------+\n"
        "| Bananas | 5        |\n"
        "+---------+----------+"
    )

    converted_table = xhtml_table_to_text(table_node, format="grid")
    assert converted_table == expected_table


def test_xhtml_table_to_text_raises_exception():
    # Create an etree element that is not a table
    non_table_node = etree.Element("{http://www.w3.org/1999/xhtml}div")

    # The function should raise an Exception when a non-table node is passed
    with pytest.raises(Exception):
        xhtml_table_to_text(non_table_node, format="grid")
