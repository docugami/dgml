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
            metadata=updated_metadata,
        )
