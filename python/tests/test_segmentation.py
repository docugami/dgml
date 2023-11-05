from dataclasses import dataclass
from pathlib import Path
import pytest

from dgml.segmentation import get_leaf_structural_chunks_str


@dataclass
class SegmentationTestData:
    input_file: Path
    output_file: Path


TEST_DATA_DIR = Path(__file__).parent / "test_data"
SEGMENTATION_TEST_DATA: list[SegmentationTestData] = [
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "simple/simple.xml",
        output_file=TEST_DATA_DIR / "simple/simple.normalized-chunks.txt",
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "article/Jane Doe.xml",
        output_file=TEST_DATA_DIR / "article/Jane Doe.normalized-chunks.txt",
    ),
]


@pytest.mark.parametrize("test_data", SEGMENTATION_TEST_DATA)
def test_segmentation(test_data: SegmentationTestData):
    with open(test_data.input_file, "r", encoding="utf-8") as input_file:
        article_shaped_file_xml = input_file.read()
        chunks = get_leaf_structural_chunks_str(article_shaped_file_xml)

        with open(test_data.output_file, "r", encoding="utf-8") as output_file:
            expected_whitespace_normalized_texts = output_file.readlines()

            assert chunks
            assert len(chunks) == len(
                expected_whitespace_normalized_texts
            ), f"Length of chunks found in {test_data.input_file} does not match expected output file {test_data.output_file}"

            for i in range(len(expected_whitespace_normalized_texts)):
                assert chunks[i].text == expected_whitespace_normalized_texts[i].strip()
