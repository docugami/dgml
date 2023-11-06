from dataclasses import dataclass
from pathlib import Path
import pytest
import yaml

from dgml_utils.segmentation import (
    DEFAULT_MIN_CHUNK_SIZE,
    DEFAULT_SUBCHUNK_TABLES,
    DEFAULT_INCLUDE_XML_TAGS,
    get_leaf_structural_chunks_str,
)


@dataclass
class SegmentationTestData:
    input_file: Path
    output_file: Path
    min_chunk_size: int = DEFAULT_MIN_CHUNK_SIZE
    sub_chunk_tables: bool = DEFAULT_SUBCHUNK_TABLES
    include_xml_tags: bool = DEFAULT_INCLUDE_XML_TAGS


TEST_DATA_DIR = Path(__file__).parent / "test_data"
SEGMENTATION_TEST_DATA: list[SegmentationTestData] = [
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "simple/simple.xml",
        output_file=TEST_DATA_DIR / "simple/simple.normalized-chunks.yaml",
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "simple/simple.xml",
        output_file=TEST_DATA_DIR / "simple/simple.normalized-chunks_xml.yaml",
        include_xml_tags=True,
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "simple/simple.xml",
        output_file=TEST_DATA_DIR / "simple/simple.normalized-chunks_all.yaml",
        min_chunk_size=0,  # want all the chunks, regardless of size
        sub_chunk_tables=True,  # want all cells inside tables chunked out
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "article/Jane Doe.xml",
        output_file=TEST_DATA_DIR / "article/Jane Doe.normalized-chunks.yaml",
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "article/Jane Doe.xml",
        output_file=TEST_DATA_DIR / "article/Jane Doe.normalized-chunks_all.yaml",
        min_chunk_size=0,  # want all the chunks, regardless of size
        sub_chunk_tables=True,  # want all cells inside tables chunked out
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "tabular/20071204X01896.xml",
        output_file=TEST_DATA_DIR / "tabular/20071204X01896.normalized-chunks.yaml",
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "tabular/20071210X01921.xml",
        output_file=TEST_DATA_DIR / "tabular/20071210X01921.normalized-chunks.yaml",
    ),
]


@pytest.mark.parametrize("test_data", SEGMENTATION_TEST_DATA)
def test_segmentation(test_data: SegmentationTestData):
    with open(test_data.input_file, "r", encoding="utf-8") as input_file:
        article_shaped_file_xml = input_file.read()
        chunks = get_leaf_structural_chunks_str(
            dgml=article_shaped_file_xml,
            min_chunk_size=test_data.min_chunk_size,
            sub_chunk_tables=test_data.sub_chunk_tables,
            include_xml_tags=test_data.include_xml_tags,
        )
        assert chunks

        with open(test_data.output_file, "r", encoding="utf-8") as output_file:
            yaml_content = yaml.safe_load(output_file)
            expected_texts = [item["text"] for item in yaml_content if "text" in item]

            for i in range(len(expected_texts)):
                assert chunks[i].text == expected_texts[i].strip()

            assert len(chunks) == len(
                expected_texts
            ), f"Length of chunks found in {test_data.input_file} does not match expected output file {test_data.output_file}"
