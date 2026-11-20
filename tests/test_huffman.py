"""Comprehensive pytest suite for Huffman Coding File Compressor."""

from __future__ import annotations

import os
import pytest

from src.file_handler import (
    compress_bytes,
    compress_file,
    decompress_bytes,
    decompress_file,
    inspect_huff_file,
    pack_bits,
    unpack_bits,
)
from src.huffman_coding import HuffmanCoding


def test_empty_string_roundtrip() -> None:
    compressed, c_stats = compress_bytes("")
    restored, d_stats = decompress_bytes(compressed)
    assert restored == ""
    assert c_stats["total_chars"] == 0
    assert d_stats["total_chars"] == 0


def test_single_character_and_repeated_single_character() -> None:
    for sample in ["a", "aaaaaaaaaaaaaaa", "🔥" * 50]:
        compressed, _ = compress_bytes(sample)
        restored, _ = decompress_bytes(compressed)
        assert restored == sample


def test_prefix_free_property() -> None:
    text = "huffman coding is an optimal prefix free lossless compression algorithm!"
    freq_map = HuffmanCoding.calculate_frequencies(text)
    root = HuffmanCoding.build_huffman_tree(freq_map)
    codes = HuffmanCoding.generate_codes(root)

    code_list = list(codes.values())
    for i, c1 in enumerate(code_list):
        for j, c2 in enumerate(code_list):
            if i != j:
                assert not c1.startswith(c2), f"Code {c2} is a prefix of {c1}"


def test_unicode_and_special_characters() -> None:
    text = "Hello World!\n\tTabs & Newlines.\nनमस्ते भारत 🇮🇳 — Café naïve résumé 日本語!"
    compressed, _ = compress_bytes(text)
    restored, _ = decompress_bytes(compressed)
    assert restored == text


def test_compression_reduces_file_size_on_prose(tmp_path) -> None:
    sample_text = (
        "Greedy algorithms make the locally optimal choice at each stage with the "
        "hope of finding a global optimum. Huffman coding proves this rigorously. "
    ) * 100

    src_file = tmp_path / "input.txt"
    huff_file = tmp_path / "output.huff"
    out_file = tmp_path / "restored.txt"
    src_file.write_text(sample_text, encoding="utf-8")

    c_stats = compress_file(str(src_file), str(huff_file))
    d_stats = decompress_file(str(huff_file), str(out_file))

    assert out_file.read_text(encoding="utf-8") == sample_text
    assert c_stats["compressed_size_bytes"] < c_stats["original_size_bytes"]
    assert c_stats["space_savings_pct"] > 35.0
    assert d_stats["restored_size_bytes"] == c_stats["original_size_bytes"]

    meta = inspect_huff_file(str(huff_file))
    assert meta["total_original_chars"] == len(sample_text)


def test_bit_packing_padding_boundaries() -> None:
    for length in range(1, 20):
        bits = "".join("1" if i % 2 == 0 else "0" for i in range(length))
        packed, pad = pack_bits(bits)
        assert 0 <= pad <= 7
        assert unpack_bits(packed, pad) == bits


def test_invalid_huff_magic_raises() -> None:
    with pytest.raises(ValueError, match="magic header"):
        decompress_bytes(b"NOT_A_HUFF_FILE_1234567890")


def test_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        compress_file("non_existent_file_xyz.txt")
    with pytest.raises(FileNotFoundError):
        decompress_file("non_existent_file_xyz.huff")
