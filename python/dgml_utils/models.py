from pydantic import BaseModel


class Chunk(BaseModel):
    tag: str
    text: str
    xml: str
    structure: str

    def __add__(self, other):
        if isinstance(other, Chunk):
            return Chunk(
                tag=self.tag + " " + other.tag,
                text=self.text + " " + other.text,
                xml=self.xml + " " + other.xml,
                structure=self.structure + " " + other.structure,
            )
        return NotImplemented
