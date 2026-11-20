"""DAA Benchmarking & Performance Analysis Module.

Generates diverse sample datasets, benchmarks Huffman compression and
decompression (size, ratio, space savings, encoding/decoding time, peak memory),
exports results to CSV, and renders publication-quality Matplotlib charts.
"""

from __future__ import annotations

import csv
import os
import random
import string
import tempfile
import tracemalloc
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .file_handler import compress_file, decompress_file

SAMPLE_PARAGRAPH = (
    "Design and Analysis of Algorithms forms the mathematical backbone of modern "
    "computer science. Huffman coding, introduced by David A. Huffman in 1952, is "
    "a classic greedy algorithm that produces an optimal prefix-free binary code "
    "for lossless data compression. By assigning shorter bit sequences to frequent "
    "symbols and longer bit sequences to rare symbols, Huffman trees minimize the "
    "expected codeword length and approach the Shannon entropy lower bound. "
)


def generate_sample_files(sample_dir: str = "sample_files") -> List[str]:
    """Create diverse test files covering size and entropy variations."""
    os.makedirs(sample_dir, exist_ok=True)
    rng = random.Random(42)

    datasets: Dict[str, str] = {
        "01_prose_1kb.txt": (SAMPLE_PARAGRAPH * 3)[:1024],
        "02_prose_10kb.txt": (SAMPLE_PARAGRAPH * 30)[:10_240],
        "03_prose_100kb.txt": (SAMPLE_PARAGRAPH * 280)[:102_400],
        "04_prose_500kb.txt": (SAMPLE_PARAGRAPH * 1400)[:512_000],
        "05_repetitive_100kb.txt": ("AAAABBBCCD" * 10_240),
        "06_random_50kb.txt": "".join(
            rng.choices(string.ascii_letters + string.digits + string.punctuation + " ", k=51_200)
        ),
        "07_unicode_multilingual.txt": (
            "Huffman Coding — डेटा संपीड़न (Data Compression) 🚀✨\n"
            "नमस्ते दुनिया! Café, naïve, résumé, 東京, Алгоритмы.\n"
        ) * 200,
    }

    paths: List[str] = []
    for filename, content in datasets.items():
        path = os.path.join(sample_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        paths.append(path)
    return paths


def run_benchmarks(
    sample_dir: str = "sample_files",
    results_dir: str = "results",
) -> List[Dict[str, object]]:
    """Run full benchmark suite, verify lossless integrity, and export CSV + charts."""
    os.makedirs(results_dir, exist_ok=True)
    sample_paths = generate_sample_files(sample_dir)

    records: List[Dict[str, object]] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for path in sample_paths:
            filename = os.path.basename(path)
            huff_path = os.path.join(tmpdir, f"{filename}.huff")
            restored_path = os.path.join(tmpdir, f"{filename}.restored.txt")

            # Measure Compression + Peak Memory
            tracemalloc.start()
            comp_stats = compress_file(path, huff_path)
            _, comp_peak_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Measure Decompression + Peak Memory
            tracemalloc.start()
            decomp_stats = decompress_file(huff_path, restored_path)
            _, decomp_peak_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Verify lossless round-trip integrity
            with open(path, "r", encoding="utf-8") as f1, open(
                restored_path, "r", encoding="utf-8"
            ) as f2:
                lossless = f1.read() == f2.read()
            if not lossless:
                raise AssertionError(f"Lossless verification failed for {filename}!")

            records.append(
                {
                    "Dataset": filename,
                    "Original Size (B)": comp_stats["original_size_bytes"],
                    "Compressed Size (B)": comp_stats["compressed_size_bytes"],
                    "Compression Ratio": comp_stats["compression_ratio"],
                    "Space Savings (%)": comp_stats["space_savings_pct"],
                    "Unique Chars": comp_stats["unique_chars"],
                    "Encode Time (ms)": comp_stats["encoding_time_ms"],
                    "Decode Time (ms)": decomp_stats["decoding_time_ms"],
                    "Peak Memory (KB)": round(max(comp_peak_bytes, decomp_peak_bytes) / 1024.0, 2),
                    "Lossless Verified": "PASS",
                }
            )

    csv_path = os.path.join(results_dir, "benchmark_results.csv")
    fieldnames = list(records[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    _plot_size_comparison(records, os.path.join(results_dir, "size_comparison.png"))
    _plot_time_complexity(records, os.path.join(results_dir, "time_complexity.png"))
    return records


def _plot_size_comparison(records: List[Dict[str, object]], output_path: str) -> None:
    """Generate Original vs. Compressed File Size bar chart."""
    labels = [str(r["Dataset"]).replace(".txt", "") for r in records]
    orig_kb = [float(r["Original Size (B)"]) / 1024.0 for r in records]
    comp_kb = [float(r["Compressed Size (B)"]) / 1024.0 for r in records]
    savings = [float(r["Space Savings (%)"]) for r in records]

    x = list(range(len(labels)))
    width = 0.36

    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=150)
    bars1 = ax.bar([i - width / 2 for i in x], orig_kb, width, label="Original Size (KB)", color="#3b82f6")
    bars2 = ax.bar([i + width / 2 for i in x], comp_kb, width, label="Compressed .huff Size (KB)", color="#10b981")

    for bar, sav in zip(bars2, savings):
        height = bar.get_height()
        ax.annotate(
            f"-{sav:.1f}%" if sav >= 0 else f"+{abs(sav):.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color="#065f46" if sav >= 0 else "#991b1b",
        )

    ax.set_ylabel("File Size (KB)", fontsize=11, fontweight="bold")
    ax.set_title("Huffman Coding: Original vs. Compressed File Size Across Datasets", fontsize=13, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=22, ha="right", fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.45)
    ax.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


def _plot_time_complexity(records: List[Dict[str, object]], output_path: str) -> None:
    """Generate Input Size vs. Execution Time line chart for prose scaling datasets."""
    prose_records = [r for r in records if "prose" in str(r["Dataset"])]
    prose_records.sort(key=lambda r: float(r["Original Size (B)"]))

    sizes_kb = [float(r["Original Size (B)"]) / 1024.0 for r in prose_records]
    enc_ms = [float(r["Encode Time (ms)"]) for r in prose_records]
    dec_ms = [float(r["Decode Time (ms)"]) for r in prose_records]

    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    ax.plot(sizes_kb, enc_ms, marker="o", linewidth=2.2, label="Encoding Time (ms)", color="#2563eb")
    ax.plot(sizes_kb, dec_ms, marker="s", linewidth=2.2, label="Decoding Time (ms)", color="#f59e0b")

    ax.set_xlabel("Input File Size (KB)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Execution Time (ms)", fontsize=11, fontweight="bold")
    ax.set_title("Empirical Time Complexity: Input Size vs. Encode/Decode Time (Linear O(N))", fontsize=12.5, fontweight="bold", pad=12)
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


if __name__ == "__main__":
    results = run_benchmarks()
    print(f"Benchmarked {len(results)} datasets successfully. Artifacts saved to results/.")
