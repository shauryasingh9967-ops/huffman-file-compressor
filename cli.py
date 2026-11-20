"""Command-Line Interface for Huffman Coding File Compressor."""

from __future__ import annotations

import argparse
import sys

from src.analyzer import run_benchmarks
from src.file_handler import compress_file, decompress_file, inspect_huff_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="huffman-cli",
        description="Lossless File Compression & Decompression using Huffman Coding (DAA Capstone).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # compress
    p_comp = subparsers.add_parser("compress", help="Compress a UTF-8 .txt file into .huff format")
    p_comp.add_argument("input", help="Path to input text file")
    p_comp.add_argument("-o", "--output", default=None, help="Output .huff file path (optional)")

    # decompress
    p_dec = subparsers.add_parser("decompress", help="Decompress a .huff file back to .txt")
    p_dec.add_argument("input", help="Path to input .huff file")
    p_dec.add_argument("-o", "--output", default=None, help="Output .txt file path (optional)")

    # inspect
    p_ins = subparsers.add_parser("inspect", help="Inspect header metadata of a .huff file")
    p_ins.add_argument("input", help="Path to .huff file")

    # benchmark
    p_bench = subparsers.add_parser("benchmark", help="Run DAA benchmark suite & generate charts")
    p_bench.add_argument("--sample-dir", default="sample_files", help="Directory for sample datasets")
    p_bench.add_argument("--results-dir", default="results", help="Directory for CSV & chart outputs")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "compress":
        stats = compress_file(args.input, args.output)
        print(f"Compressed successfully: {stats['output_path']}")
        print(f"  Original Size   : {stats['original_size_bytes']:,} bytes")
        print(f"  Compressed Size : {stats['compressed_size_bytes']:,} bytes "
              f"(Header: {stats['header_size_bytes']} B, Payload: {stats['payload_size_bytes']} B)")
        print(f"  Compression Ratio: {stats['compression_ratio']:.4f}")
        print(f"  Space Savings   : {stats['space_savings_pct']:.2f}%")
        print(f"  Encoding Time   : {stats['encoding_time_ms']:.3f} ms")
        return 0

    if args.command == "decompress":
        stats = decompress_file(args.input, args.output)
        print(f"Decompressed successfully: {stats['output_path']}")
        print(f"  Compressed Size : {stats['compressed_size_bytes']:,} bytes")
        print(f"  Restored Size   : {stats['restored_size_bytes']:,} bytes")
        print(f"  Decoding Time   : {stats['decoding_time_ms']:.3f} ms")
        return 0

    if args.command == "inspect":
        meta = inspect_huff_file(args.input)
        print(f"Metadata for {meta['file_path']}:")
        for k, v in meta.items():
            if k != "file_path":
                print(f"  {k}: {v}")
        return 0

    if args.command == "benchmark":
        records = run_benchmarks(sample_dir=args.sample_dir, results_dir=args.results_dir)
        header = f"{'Dataset':<28} {'Orig(B)':>10} {'Comp(B)':>10} {'Saved%':>8} {'Enc(ms)':>9} {'Dec(ms)':>9} {'Mem(KB)':>9}"
        print(header)
        print("-" * len(header))
        for r in records:
            print(
                f"{str(r['Dataset']):<28} {int(r['Original Size (B)']):>10,} "
                f"{int(r['Compressed Size (B)']):>10,} {float(r['Space Savings (%)']):>7.2f}% "
                f"{float(r['Encode Time (ms)']):>9.2f} {float(r['Decode Time (ms)']):>9.2f} "
                f"{float(r['Peak Memory (KB)']):>9.2f}"
            )
        print(f"\nCSV and Matplotlib charts saved in: {args.results_dir}/")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
