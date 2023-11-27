from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


def merge_parents(ours: Optional[Chunk], theirs: Optional[Chunk]) -> Optional[Chunk]:
    """
    Merges two parent Chunks, choosing the one with the longer text or one if the other is None.

    >>> parent1 = Chunk(tag='p', text='Longer text here', xml='', structure='', xpath='')
    >>> parent2 = Chunk(tag='p', text='Short', xml='', structure='', xpath='')
    >>> merge_parents(parent1, parent2) is parent1
    True
    >>> merge_parents(parent2, None) is parent2
    True
    """
    if ours is None:
        return theirs
    if theirs is None:
        return ours
    return ours if len(ours.text) >= len(theirs.text) else theirs


def merge_xpaths(ours: str, theirs: str):
    """
    Merges two xpaths, returning the shorter one.

    >>> merge_xpaths('/a[1]', '/b[1]/c')
    '/a[1]'
    >>> merge_xpaths('/a[1]/b[2]', '/b[1]')
    '/b[1]'
    """
    return ours if len(ours) <= len(theirs) else theirs


def merge_tags(ours: str, theirs: str):
    """
    Merges two sets of tags, returning the concatenation if disjoint
    or the larger one if one is a subset of the other.

    >>> merge_tags('lim', 'h1')
    'lim h1'
    >>> merge_tags('lim h1', 'h1 ')
    'lim h1'
    >>> merge_tags('lim h1 div', 'lim div')
    'lim h1 div'
    >>> merge_tags('lim h1 div', '')
    'lim h1 div'
    """
    # Split tags by spaces to work with them as sets
    our_tags = set(ours.split())
    their_tags = set(theirs.split())

    # If one is a subset of the other, return the larger one
    if our_tags.issubset(their_tags):
        return theirs
    if their_tags.issubset(our_tags):
        return ours

    # If disjoint, return the concatenation
    return ours + " " + theirs if ours and theirs else ours or theirs


@dataclass
class Chunk:
    tag: str
    text: str
    xml: str
    structure: str
    xpath: str
    parent: Optional[Chunk] = None
    bboxes: List[BoundingBox] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def __add__(self, other: Chunk):
        """
        Adds another Chunk object to this one and returns a new Chunk object.

        >>> chunk1 = Chunk(tag='a', text='Hello', xml='<a>Hello</a>', structure='', xpath='/a[1]', parent=None)
        >>> chunk2 = Chunk(tag='b', text='World!', xml='<b>World!</b>', structure='', xpath='/b[1]', parent=None)
        >>> chunk3 = chunk1 + chunk2
        >>> chunk3.text
        'Hello World!'
        >>> chunk3.xpath
        '/a[1]'
        """

        # Ensure that 'other' is indeed an instance of Chunk before proceeding.
        if not isinstance(other, Chunk):
            return NotImplemented

        # Update the metadata first since we will use it when creating the new Chunk instance.
        # This ensures that 'self.metadata' is not modified in-place.
        updated_metadata = {**self.metadata, **other.metadata}

        return Chunk(
            tag=merge_tags(self.tag, other.tag),
            text=self.text + " " + other.text,
            xml=self.xml + " " + other.xml,
            structure=(self.structure + " " + other.structure).strip(),
            xpath=merge_xpaths(self.xpath, other.xpath),
            parent=merge_parents(self.parent, other.parent),
            bboxes=self.bboxes + other.bboxes,
            metadata=updated_metadata,
        )


class BoundingBox:
    """The origin (0,0) for these bounding boxes is in the top, left
    of the image/page."""

    def __init__(self, left: float, top: float, right: float, bottom: float, page: Optional[int] = None):
        self.left: float = left
        self.top: float = top
        self.right: float = right
        self.bottom: float = bottom
        self.page: Optional[int] = page

        if not self.is_valid():
            raise ValueError(f"Invalid bounding box: {self}")

    def clone(self) -> BoundingBox:
        return BoundingBox(self.left, self.top, self.right, self.bottom, self.page)

    def is_valid(self) -> bool:
        if self.page == 0:
            return False

        if self.is_empty:
            return True

        return self.left < self.right and self.top < self.bottom

    @property
    def is_empty(self) -> bool:
        return self.left == self.right == self.top == self.bottom == 0

    def union(self, other: BoundingBox) -> BoundingBox:
        if self.is_empty:
            return other.clone()

        if other.is_empty:
            return self.clone()

        left = min(self.left, other.left)
        top = min(self.top, other.top)
        right = max(self.right, other.right)
        bottom = max(self.bottom, other.bottom)
        return BoundingBox(left, top, right, bottom, self.page)

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top

    def __str__(self):
        str_output = (
            str(self.left) + " " + str(self.top) + " " + str(self.right) + " " + str(self.bottom) + " " + str(self.page)
        )
        return str_output

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other):
        """Overrides the default implementation, ne will default to use eq"""
        if isinstance(other, BoundingBox):
            return (
                self.left == other.left
                and self.right == other.right
                and self.top == other.top
                and self.bottom == other.bottom
                and self.page == other.page
            )
        return False

    @classmethod
    def from_style(cls, style: str) -> List[BoundingBox]:
        """
        Builds a list of bounding boxes from a DGML style attribute value.
        The style string can contain various attributes, but must include
        'left', 'top', 'width', and 'height' for each bounding box. Optionally, 'page' can be included.

        Doctests:
        >>> style_single = "boundingBox:{left: 201.0; top: 592.6; width: 2145.0; height: 415.8; page: 1;}"
        >>> BoundingBox.from_style(style_single)
        [201.0 592.6 2346.0 1008.4 1]

        >>> style_multiple = "list-style-type: decimal; boundingBox:{left: 300.0; top: 936.0; width: 30.0; height: 1881.0; page: 1;}; boundingBox:{left: 300.0; top: 309.0; width: 30.0; height: 777.0; page: 2;};"
        >>> BoundingBox.from_style(style_multiple)
        [300.0 936.0 330.0 2817.0 1, 300.0 309.0 330.0 1086.0 2]
        """
        if not style:
            return []

        # Split the style string into individual bounding box declarations
        bounding_boxes = style.split("boundingBox:")
        bounding_boxes = [box for box in bounding_boxes if box.strip()]

        result = []
        for box in bounding_boxes:
            # Process each bounding box block
            box = box.strip("{} \t\n;")

            # Extract key-value pairs
            parts = box.split(";")

            values = {}
            for part in parts:
                key_value = part.split(":")
                if len(key_value) == 2:
                    key, value = key_value
                    key = key.strip().lower()  # Normalize the key
                    try:
                        values[key] = float(value.strip())
                    except ValueError:
                        continue  # Skip invalid entries

            # Check for required keys and calculate right and bottom
            try:
                left = values["left"]
                top = values["top"]
                width = values["width"]
                height = values["height"]
            except KeyError:
                continue  # Skip if required key not found

            right = round(left + width, 1)
            bottom = round(top + height, 1)
            page = values.get("page")

            # Create and add the BoundingBox object to the result
            result.append(
                BoundingBox(
                    left,
                    top,
                    right,
                    bottom,
                    int(page) if page is not None else None,
                )
            )

        return result
