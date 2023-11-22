from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional


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


def merge_bboxes(ours: Optional[BoundingBox], theirs: Optional[BoundingBox]) -> Optional[BoundingBox]:
    """
    Merges two bboxes, doing a union if both set or one if the other is None.

    >>> bbox1 = BoundingBox(left=1, top=1, right=3, bottom=3, page=1)
    >>> bbox2 = BoundingBox(left=1, top=1, right=4, bottom=5, page=1)
    >>> merge_bboxes(bbox1, bbox2)
    1 1 4 5 1
    """
    if ours is None:
        return theirs
    if theirs is None:
        return ours
    return ours.union(theirs)


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
    bbox: Optional[BoundingBox] = None
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
            bbox=merge_bboxes(self.bbox, other.bbox),
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
    def from_style(cls, style: str) -> Optional[BoundingBox]:
        """
        Builds a bounding box from a DGML style attribute value.

        The style string can contain various attributes, but must include
        'left', 'top', 'width', and 'height'. Optionally, 'page' can be included.

        Doctests:
        >>> style = "boundingBox:{left: 201.0; top: 592.6; width: 2145.0; height: 415.8; page: 1;}  "
        >>> BoundingBox.from_style(style)
        201.0 592.6 2346.0 1008.4 1
        """
        if not style or ";" not in style or ":" not in style:
            return None

        # Remove leading/trailing text
        style = style.replace("boundingBox:", "")
        style = style.strip("{} \t\n")

        # Extract key-value pairs
        parts = style.split(";")

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
            return None  # Required key not found

        right = round(left + width, 1)
        bottom = round(top + height, 1)
        page = values.get("page")

        # Create and return the BoundingBox object
        return BoundingBox(
            left,
            top,
            right,
            bottom,
            int(page) if page is not None else None,
        )
