from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import pytest
import yaml

from dgml_utils.segmentation import (
    DEFAULT_MIN_CHUNK_LENGTH,
    DEFAULT_SUBCHUNK_TABLES,
    DEFAULT_INCLUDE_XML_TAGS,
    DEFAULT_XML_HIERARCHY_LEVELS,
    get_leaf_structural_chunks_str,
)
from dgml_utils.models import Chunk


@dataclass
class SegmentationTestData:
    input_file: Path
    output_file: Path
    min_chunk_length: int = DEFAULT_MIN_CHUNK_LENGTH
    sub_chunk_tables: bool = DEFAULT_SUBCHUNK_TABLES
    include_xml_tags: bool = DEFAULT_INCLUDE_XML_TAGS
    xml_hierarchy_levels: int = DEFAULT_XML_HIERARCHY_LEVELS


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
        xml_hierarchy_levels=3,
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "simple/simple.xml",
        output_file=TEST_DATA_DIR / "simple/simple.normalized-chunks_all.yaml",
        min_chunk_length=0,  # want all the chunks, regardless of length
        sub_chunk_tables=True,  # want all cells inside tables chunked out
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "article/Jane Doe.xml",
        output_file=TEST_DATA_DIR / "article/Jane Doe.normalized-chunks.yaml",
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "article/Jane Doe.xml",
        output_file=TEST_DATA_DIR / "article/Jane Doe.normalized-chunks_all.yaml",
        min_chunk_length=0,  # want all the chunks, regardless of length
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
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "arxiv/2307.09288.xml",
        output_file=TEST_DATA_DIR / "arxiv/2307.09288.normalized-chunks.yaml",
    ),
]


def _debug_dump_yaml(chunks: List[Chunk], output_path: Optional[Path] = None):
    """
    Use this in the debugger to dump yaml to a path for inspection or bootstrapping test cases.
    """
    yaml_lines = []
    for chunk in chunks:
        if chunk.tag == "table":
            yaml_lines.append("- text: |")
            for row in chunk.text.splitlines():
                yaml_lines.append(f"    {row}")
        else:
            text = chunk.text.replace('"', '\\"')  # Escape double quotes
            yaml_lines.append(f'- text: "{text}"')

        yaml_lines.append(f'  tag: "{chunk.tag}"')
        yaml_lines.append(f'  structure: "{chunk.structure}"')

    yaml = "\n".join(yaml_lines)

    if output_path:
        with open(output_path, "w") as file:
            file.write(yaml)
    else:
        print(yaml)


@pytest.mark.parametrize("test_data", SEGMENTATION_TEST_DATA)
def test_segmentation(test_data: SegmentationTestData):
    with open(test_data.input_file, "r", encoding="utf-8") as input_file:
        article_shaped_file_xml = input_file.read()
        chunks = get_leaf_structural_chunks_str(
            dgml=article_shaped_file_xml,
            min_chunk_length=test_data.min_chunk_length,
            sub_chunk_tables=test_data.sub_chunk_tables,
            include_xml_tags=test_data.include_xml_tags,
            xml_hierarchy_levels=test_data.xml_hierarchy_levels,
        )
        assert chunks

        with open(test_data.output_file, "r", encoding="utf-8") as output_file:
            yaml_content = yaml.safe_load(output_file)
            expected_chunks = [item for item in yaml_content if "text" in item]

            for i in range(len(expected_chunks)):
                assert chunks[i].text == expected_chunks[i]["text"].strip()
                if "parent_3_text" in expected_chunks[i]:
                    assert chunks[i].parent
                    assert chunks[i].parent.text == expected_chunks[i]["parent_3_text"].strip()  # type: ignore
                if "xpath" in expected_chunks[i]:
                    assert chunks[i].xpath == expected_chunks[i]["xpath"].strip()
                if "tag" in expected_chunks[i]:
                    assert chunks[i].tag == expected_chunks[i]["tag"].strip()
                if "structure" in expected_chunks[i]:
                    assert chunks[i].structure == expected_chunks[i]["structure"].strip()

            assert len(chunks) == len(
                expected_chunks
            ), f"Length of chunks found in {test_data.input_file} does not match expected output file {test_data.output_file}"
