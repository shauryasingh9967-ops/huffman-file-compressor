"""Huffman Coding Lossless File Compression Package."""

from .huffman_node import HuffmanNode
from .huffman_coding import HuffmanCoding
from .file_handler import compress_file, decompress_file, compress_bytes, decompress_bytes

__all__ = [
    "HuffmanNode",
    "HuffmanCoding",
    "compress_file",
    "decompress_file",
    "compress_bytes",
    "decompress_bytes",
]
