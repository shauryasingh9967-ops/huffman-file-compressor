"""Huffman Tree Node implementation for Min-Heap priority queue operations."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class HuffmanNode:
    """Represents a node in the Huffman Binary Tree.

    Attributes:
        freq: Frequency count of the character or combined subtree.
        char: Single character for leaf nodes; None for internal nodes.
        left: Left child node (represents bit '0').
        right: Right child node (represents bit '1').
    """

    freq: int
    char: Optional[str] = None
    left: Optional[HuffmanNode] = None
    right: Optional[HuffmanNode] = None

    def is_leaf(self) -> bool:
        """Return True if this node is a leaf node."""
        return self.left is None and self.right is None

    def __lt__(self, other: HuffmanNode) -> bool:
        """Compare nodes by frequency for heapq Min-Heap ordering.

        Deterministic tie-breaking uses character code point so trees are
        reproducible across runs.
        """
        if self.freq != other.freq:
            return self.freq < other.freq
        self_key = "" if self.char is None else self.char
        other_key = "" if other.char is None else other.char
        return self_key < other_key

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HuffmanNode):
            return NotImplemented
        return (
            self.freq == other.freq
            and self.char == other.char
            and self.left == other.left
            and self.right == other.right
        )
