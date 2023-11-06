from typing import Dict
from pydantic import BaseModel

from dgml_utils.conversions import clean_tag


class Chunk(BaseModel):
    tag: str
    text: str
    xml: str
    structure: str
    xpath: str
    metadata: Dict = {}

    def __add__(self, other):
        def merge_strings(ours, theirs):
            if theirs in ours:
                return ours  # ours already contains theirs as a substripg

            return (ours + " " + theirs).strip()

        if isinstance(other, Chunk):
            return Chunk(
                tag=merge_strings(clean_tag(self), clean_tag(other)),
                text=self.text + " " + other.text,
                xml=self.xml + " " + other.xml,
                structure=self.structure + " " + other.structure,
                xpath=other.xpath,  # TODO: Decide how to merge xpaths, for now overwriting
                metadata=self.metadata.update(other.metadata) or {},
            )
        return NotImplemented
