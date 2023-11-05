from pydantic import BaseModel


class Chunk(BaseModel):
    tag: str
    text: str
    xml: str
    structure: str
