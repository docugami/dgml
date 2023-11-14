from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import pytest
import yaml
from dgml_utils.config import DEFAULT_MAX_TEXT_LENGTH

from dgml_utils.segmentation import (
    DEFAULT_MIN_TEXT_LENGTH,
    DEFAULT_SUBCHUNK_TABLES,
    DEFAULT_XML_MODE,
    DEFAULT_PARENT_HIERARCHY_LEVELS,
    get_chunks_str,
)
from dgml_utils.models import Chunk


@dataclass
class SegmentationTestData:
    input_file: Path
    output_file: Path
    min_text_length: int = DEFAULT_MIN_TEXT_LENGTH
    max_text_length: int = DEFAULT_MAX_TEXT_LENGTH
    sub_chunk_tables: bool = DEFAULT_SUBCHUNK_TABLES
    xml_mode: bool = DEFAULT_XML_MODE
    parent_hierarchy_levels: int = DEFAULT_PARENT_HIERARCHY_LEVELS


TEST_DATA_DIR = Path(__file__).parent / "test_data"
SEGMENTATION_TEST_DATA: list[SegmentationTestData] = [
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "fake/fake.xml",
        output_file=TEST_DATA_DIR / "fake/fake.chunks_text.yaml",
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "fake/fake.xml",
        output_file=TEST_DATA_DIR / "fake/fake.chunks_text_p3.yaml",
        xml_mode=False,
        parent_hierarchy_levels=3,
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "fake/fake.xml",
        output_file=TEST_DATA_DIR / "fake/fake.chunks_xml_p3.yaml",
        max_text_length=232,  # size of the <ConfidentialityObligations> chunk
        xml_mode=True,
        parent_hierarchy_levels=3,
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "fake/fake.xml",
        output_file=TEST_DATA_DIR / "fake/fake.chunks_text_min0.yaml",
        min_text_length=0,  # Want all the chunks separated out, regardless of length
        sub_chunk_tables=True,  # Want all cells inside tables chunked out
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "article/Jane Doe.xml",
        output_file=TEST_DATA_DIR / "article/Jane Doe.chunks_text.yaml",
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "article/Jane Doe.xml",
        output_file=TEST_DATA_DIR / "article/Jane Doe.chunks_text_min0.yaml",
        min_text_length=0,  # Want all the chunks separated out, regardless of length
        sub_chunk_tables=True,  # Want all cells inside tables chunked out
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "tabular/20071204X01896.xml",
        output_file=TEST_DATA_DIR / "tabular/20071204X01896.chunks_text.yaml",
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "tabular/20071210X01921.xml",
        output_file=TEST_DATA_DIR / "tabular/20071210X01921.chunks_text.yaml",
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "arxiv/2307.09288.xml",
        output_file=TEST_DATA_DIR / "arxiv/2307.09288.chunks_text.yaml",
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "article/Shorebucks LLC_AZ.xml",
        output_file=TEST_DATA_DIR / "article/Shorebucks LLC_AZ.chunks_text.yaml",
    ),
    SegmentationTestData(
        input_file=TEST_DATA_DIR / "article/Shorebucks LLC_AZ.xml",
        output_file=TEST_DATA_DIR / "article/Shorebucks LLC_AZ.chunks_text_xml_min32_p3.yaml",
        min_text_length=32,
        xml_mode=True,
        parent_hierarchy_levels=3,
    ),
]


def _debug_dump_yaml(chunks: List[Chunk], output_path: Optional[Path] = None):
    """
    Use this in the debugger to dump yaml to a path for inspection or bootstrapping test cases.
    """
    yaml_lines = []
    for chunk in chunks:
        text = chunk.text
        lines = text.splitlines()
        if lines:
            yaml_lines.append("- text: |")
            for line in lines:
                yaml_lines.append(f"    {line}")

        if chunk.parent:
            yaml_lines.append("  parent_text: |")
            for parent_chunk_line in chunk.parent.text.splitlines():
                yaml_lines.append(f"    {parent_chunk_line}")

        yaml_lines.append(f'  tag: "{chunk.tag}"')
        yaml_lines.append(f'  structure: "{chunk.structure}"')
        yaml_lines.append(f'  xpath: "{chunk.xpath}"')

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
        chunks = get_chunks_str(
            dgml=article_shaped_file_xml,
            min_text_length=test_data.min_text_length,
            max_text_length=test_data.max_text_length,
            sub_chunk_tables=test_data.sub_chunk_tables,
            xml_mode=test_data.xml_mode,
            parent_hierarchy_levels=test_data.parent_hierarchy_levels,
        )
        assert chunks

        with open(test_data.output_file, "r", encoding="utf-8") as output_file:
            yaml_content = yaml.safe_load(output_file)
            expected_chunks = [item for item in yaml_content if "text" in item]

            for i in range(len(expected_chunks)):
                assert chunks[i].text == expected_chunks[i]["text"].strip()
                if "parent_text" in expected_chunks[i]:
                    assert chunks[i].parent
                    assert chunks[i].parent.text == expected_chunks[i]["parent_text"].strip()  # type: ignore
                if "xpath" in expected_chunks[i]:
                    assert chunks[i].xpath == expected_chunks[i]["xpath"].strip()
                if "tag" in expected_chunks[i]:
                    assert chunks[i].tag == expected_chunks[i]["tag"].strip()
                if "structure" in expected_chunks[i]:
                    assert chunks[i].structure == expected_chunks[i]["structure"].strip()

            assert len(chunks) == len(
                expected_chunks
            ), f"Length of chunks found in {test_data.input_file} does not match expected output file {test_data.output_file}"
