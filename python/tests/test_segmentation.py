import pytest

from dgml.segmentation import get_leaf_structural_chunks_str


@pytest.fixture
def simple_dgml():
    return """
        <chunk>
            <chunk structure="h1">
                Main Heading with
                <CompanyName>Acme Corp</CompanyName>
                as mixed content
            </chunk>
            <chunk structure="div">
                <chunk structure="h1">Sub-Heading</chunk>
                <chunk structure="div">
                    Paragraph with sub-elements like <Date>Jan 1, 2023</Date>
                    and <SignatoryName>John Doe</SignatoryName> as mixed content.
                </chunk>
            </chunk>
            <ConfidentialityObligations structure="div">
                <chunk structure="div">
                    These are some obligations:
                </chunk>
                <Obligations structure="ol">
                    <Obligation structure="li">
                        <chunk structure="lim">1. </chunk>
                        <chunk structure="div">Item A</chunk>
                    </Obligation>
                    <Obligation structure="li">
                        <chunk structure="lim">2. </chunk>
                        <chunk structure="div">Item B</chunk>
                    </Obligation>
                    <Obligation structure="li">
                        <chunk structure="lim">3. </chunk>
                        <chunk structure="div">C</chunk>
                    </Obligation>
                </Obligations>
            </ConfidentialityObligations>
            <Footer structure="div">pg.1</Footer>
        </chunk>
    """


def test_simple_text_segmentation(simple_dgml):
    chunks = get_leaf_structural_chunks_str(simple_dgml)

    # We expect the following exact leaf structural text chunks (whitespace normalized)
    # based on the simple DGML
    expected_whitespace_normalized_texts = [
        "Main Heading with Acme Corp as mixed content",
        "Sub-Heading",
        "Paragraph with sub-elements like Jan 1, 2023 and John Doe as mixed content.",
        "These are some obligations:",
        "1. Item A",
        "2. Item B",
        "3. C pg.1",
    ]

    assert chunks
    assert len(chunks) == len(expected_whitespace_normalized_texts)

    for i in range(len(expected_whitespace_normalized_texts)):
        whitespace_normalized_chunk_text = " ".join(chunks[i].text.split())
        assert whitespace_normalized_chunk_text == expected_whitespace_normalized_texts[i]
