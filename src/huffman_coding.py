"""Core Huffman Coding algorithm: frequency counting, tree construction,
prefix-free code generation, encoding, and decoding.
"""

from __future__ import annotations

import heapq
from collections import Counter
from typing import Dict, Optional

from .huffman_node import HuffmanNode


class HuffmanCoding:
    """Implements lossless Huffman Coding compression and decompression."""

    @staticmethod
    def calculate_frequencies(text: str) -> Dict[str, int]:
        """Count the frequency of each character in the input text.

        Time Complexity: O(N), where N is the length of text.
        Space Complexity: O(K), where K is the number of unique characters.
        """
        return dict(Counter(text))

    @staticmethod
    def build_huffman_tree(freq_map: Dict[str, int]) -> Optional[HuffmanNode]:
        """Construct an optimal Huffman Tree using a Min-Heap.

        Time Complexity: O(K log K), where K is the number of unique characters.
        Space Complexity: O(K) for the heap and 2K - 1 tree nodes.
        """
        if not freq_map:
            return None

        # Sort items for deterministic heap construction across Python runs
        heap: list[HuffmanNode] = [
            HuffmanNode(freq=freq, char=char)
            for char, freq in sorted(freq_map.items())
        ]
        heapq.heapify(heap)

        # Edge case: single unique character
        if len(heap) == 1:
            return heap[0]

        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            merged = HuffmanNode(
                freq=left.freq + right.freq,
                char=None,
                left=left,
                right=right,
            )
            heapq.heappush(heap, merged)

        return heap[0]

    @staticmethod
    def generate_codes(root: Optional[HuffmanNode]) -> Dict[str, str]:
        """Generate optimal prefix-free binary codes via DFS traversal.

        Left edge -> '0', Right edge -> '1'.
        For a single-character input, assigns code '0'.

        Time Complexity: O(K) nodes visited (output size bounded by O(K * L_max)).
        Space Complexity: O(K) for recursion stack and code dictionary.
        """
        if root is None:
            return {}

        if root.is_leaf():
            assert root.char is not None
            return {root.char: "0"}

        codes: Dict[str, str] = {}

        def _traverse(node: Optional[HuffmanNode], prefix: str) -> None:
            if node is None:
                return
            if node.is_leaf():
                assert node.char is not None
                codes[node.char] = prefix
                return
            _traverse(node.left, prefix + "0")
            _traverse(node.right, prefix + "1")

        _traverse(root, "")
        return codes

    @staticmethod
    def encode_text(text: str, codes: Dict[str, str]) -> str:
        """Encode text into a bit-string using the generated Huffman codes.

        Time Complexity: O(N * L_avg), linear in total output bits.
        """
        if not text:
            return ""
        return "".join(codes[ch] for ch in text)

    @staticmethod
    def decode_bits(
        bit_string: str,
        root: Optional[HuffmanNode],
        total_chars: int,
    ) -> str:
        """Decode a bit-string back into original text by traversing the Huffman Tree.

        Args:
            bit_string: String of '0' and '1' characters (with padding already removed).
            root: Root node of the reconstructed Huffman Tree.
            total_chars: Exact number of characters in the original text.

        Time Complexity: O(B), where B is the number of encoded bits.
        """
        if total_chars == 0 or root is None:
            return ""

        # Edge case: single unique character repeated total_chars times
        if root.is_leaf():
            assert root.char is not None
            return root.char * total_chars

        decoded_chars: list[str] = []
        current = root

        for bit in bit_string:
            current = current.left if bit == "0" else current.right
            if current is None:
                raise ValueError("Invalid bitstream: reached null node during decoding.")
            if current.is_leaf():
                assert current.char is not None
                decoded_chars.append(current.char)
                current = root
                if len(decoded_chars) == total_chars:
                    break

        if len(decoded_chars) != total_chars:
            raise ValueError(
                f"Decoded character count mismatch: expected {total_chars}, got {len(decoded_chars)}."
            )

        return "".join(decoded_chars)
