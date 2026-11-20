"""Binary file handler (.huff format) with true bit-level packing and header serialization.

Custom .huff Binary Format Specification:
-----------------------------------------
[4 bytes]  Magic bytes: b'HUFF'
[1 byte]   Format version: 1
[1 byte]   Padding bits added to final payload byte (0..7)
[8 bytes]  Original total character count (unsigned 64-bit big-endian, >Q)
[4 bytes]  Number of unique characters K (unsigned 32-bit big-endian, >I)
For each of K unique characters:
    [1 byte]  UTF-8 byte length L of character (1..4)
    [L bytes] UTF-8 encoded character
    [4 bytes] Character frequency (unsigned 32-bit big-endian, >I)
[Remaining bytes] Bit-packed Huffman encoded payload
"""

from __future__ import annotations

import os
import struct
import time
from typing import Any, Dict, Tuple

from .huffman_coding import HuffmanCoding

MAGIC = b"HUFF"
VERSION = 1

# Precomputed byte-to-8-bit-string lookup table for fast decoding
_BYTE_TO_BITS: tuple[str, ...] = tuple(f"{i:08b}" for i in range(256))


def pack_bits(bit_string: str) -> Tuple[bytes, int]:
    """Pack a string of '0'/'1' bits into actual bytes with trailing zero padding.

    Returns:
        (packed_bytes, padding_length)
    """
    if not bit_string:
        return b"", 0

    padding = (8 - (len(bit_string) % 8)) % 8
    padded = bit_string + ("0" * padding)
    num_bytes = len(padded) // 8
    packed = int(padded, 2).to_bytes(num_bytes, byteorder="big")
    return packed, padding


def unpack_bits(data: bytes, padding: int) -> str:
    """Unpack bytes back into a bit-string and strip trailing padding bits."""
    if not data:
        return ""
    if not (0 <= padding <= 7):
        raise ValueError(f"Invalid padding value in header: {padding}")

    bit_string = "".join(_BYTE_TO_BITS[b] for b in data)
    if padding > 0:
        bit_string = bit_string[:-padding]
    return bit_string


def serialize_header(
    freq_map: Dict[str, int],
    total_chars: int,
    padding: int,
) -> bytes:
    """Serialize metadata and frequency table into compact binary header."""
    parts: list[bytes] = [
        MAGIC,
        struct.pack(">BBQ I", VERSION, padding, total_chars, len(freq_map)),
    ]
    for char, freq in sorted(freq_map.items()):
        char_bytes = char.encode("utf-8")
        parts.append(struct.pack(">B", len(char_bytes)))
        parts.append(char_bytes)
        parts.append(struct.pack(">I", freq))
    return b"".join(parts)


def deserialize_header(raw_bytes: bytes) -> Tuple[Dict[str, int], int, int, int]:
    """Parse binary header from a .huff byte stream.

    Returns:
        (freq_map, total_chars, padding, payload_offset)
    """
    min_header_size = 4 + 1 + 1 + 8 + 4  # 18 bytes
    if len(raw_bytes) < min_header_size:
        raise ValueError("Invalid .huff file: file is too short.")

    if raw_bytes[:4] != MAGIC:
        raise ValueError("Invalid .huff file: unrecognized magic header.")

    version, padding, total_chars, num_unique = struct.unpack(">BBQ I", raw_bytes[4:18])
    if version != VERSION:
        raise ValueError(f"Unsupported .huff format version: {version}")

    offset = 18
    freq_map: Dict[str, int] = {}

    for _ in range(num_unique):
        if offset >= len(raw_bytes):
            raise ValueError("Corrupted .huff header: unexpected EOF.")
        char_len = raw_bytes[offset]
        offset += 1
        char_bytes = raw_bytes[offset : offset + char_len]
        offset += char_len
        if offset + 4 > len(raw_bytes):
            raise ValueError("Corrupted .huff header: missing frequency field.")
        (freq,) = struct.unpack(">I", raw_bytes[offset : offset + 4])
        offset += 4
        freq_map[char_bytes.decode("utf-8")] = freq

    return freq_map, total_chars, padding, offset


def compress_bytes(text: str) -> Tuple[bytes, Dict[str, Any]]:
    """Compress a UTF-8 string into .huff binary bytes and return detailed stats."""
    start = time.perf_counter()

    original_bytes = text.encode("utf-8")
    freq_map = HuffmanCoding.calculate_frequencies(text)
    root = HuffmanCoding.build_huffman_tree(freq_map)
    codes = HuffmanCoding.generate_codes(root)
    bit_string = HuffmanCoding.encode_text(text, codes)
    packed_payload, padding = pack_bits(bit_string)
    header = serialize_header(freq_map, len(text), padding)
    compressed_data = header + packed_payload

    elapsed_ms = (time.perf_counter() - start) * 1000.0
    orig_size = len(original_bytes)
    comp_size = len(compressed_data)
    ratio = (comp_size / orig_size) if orig_size > 0 else 0.0
    savings_pct = ((1.0 - ratio) * 100.0) if orig_size > 0 else 0.0

    stats: Dict[str, Any] = {
        "original_size_bytes": orig_size,
        "compressed_size_bytes": comp_size,
        "header_size_bytes": len(header),
        "payload_size_bytes": len(packed_payload),
        "compression_ratio": round(ratio, 4),
        "space_savings_pct": round(savings_pct, 2),
        "unique_chars": len(freq_map),
        "total_chars": len(text),
        "padding_bits": padding,
        "encoding_time_ms": round(elapsed_ms, 3),
        "freq_map": freq_map,
        "codes": codes,
    }
    return compressed_data, stats


def decompress_bytes(data: bytes) -> Tuple[str, Dict[str, Any]]:
    """Decompress .huff binary bytes back into the original UTF-8 text."""
    start = time.perf_counter()

    freq_map, total_chars, padding, payload_offset = deserialize_header(data)
    root = HuffmanCoding.build_huffman_tree(freq_map)
    payload = data[payload_offset:]
    bit_string = unpack_bits(payload, padding)
    decoded_text = HuffmanCoding.decode_bits(bit_string, root, total_chars)

    elapsed_ms = (time.perf_counter() - start) * 1000.0
    stats: Dict[str, Any] = {
        "compressed_size_bytes": len(data),
        "restored_size_bytes": len(decoded_text.encode("utf-8")),
        "unique_chars": len(freq_map),
        "total_chars": total_chars,
        "decoding_time_ms": round(elapsed_ms, 3),
    }
    return decoded_text, stats


def compress_file(input_path: str, output_path: str | None = None) -> Dict[str, Any]:
    """Read a UTF-8 text file, compress it, and write a .huff binary file."""
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if output_path is None:
        output_path = f"{os.path.splitext(input_path)[0]}.huff"

    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    compressed_data, stats = compress_bytes(text)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(compressed_data)

    stats["input_path"] = input_path
    stats["output_path"] = output_path
    return stats


def decompress_file(input_path: str, output_path: str | None = None) -> Dict[str, Any]:
    """Read a .huff binary file, decode it, and write the restored .txt file."""
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Compressed file not found: {input_path}")

    if output_path is None:
        base, _ = os.path.splitext(input_path)
        output_path = f"{base}_decoded.txt"

    with open(input_path, "rb") as f:
        raw_bytes = f.read()

    decoded_text, stats = decompress_bytes(raw_bytes)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(decoded_text)

    stats["input_path"] = input_path
    stats["output_path"] = output_path
    return stats


def inspect_huff_file(input_path: str) -> Dict[str, Any]:
    """Inspect metadata of a .huff file without fully decoding it."""
    with open(input_path, "rb") as f:
        raw_bytes = f.read()
    freq_map, total_chars, padding, payload_offset = deserialize_header(raw_bytes)
    return {
        "file_path": input_path,
        "total_file_bytes": len(raw_bytes),
        "header_bytes": payload_offset,
        "payload_bytes": len(raw_bytes) - payload_offset,
        "total_original_chars": total_chars,
        "unique_chars": len(freq_map),
        "padding_bits": padding,
    }
