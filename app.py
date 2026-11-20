"""Interactive Streamlit Web Dashboard for Huffman Coding File Compression."""

from __future__ import annotations

import csv
import os
import streamlit as st

from src.analyzer import run_benchmarks
from src.file_handler import compress_bytes, decompress_bytes

st.set_page_config(
    page_title="Huffman File Compressor — DAA Capstone",
    page_icon="📦",
    layout="wide",
)

st.title("📦 File Compression Using Huffman Coding")
st.caption("Design and Analysis of Algorithms (DAA) Capstone Project — Lossless Bit-Level Compression")

tab_compress, tab_decompress, tab_benchmarks = st.tabs(
    ["🗜️ Compress (.txt → .huff)", "📂 Decompress (.huff → .txt)", "📊 DAA Benchmarks & Complexity"]
)

with tab_compress:
    st.subheader("Compress a Text File")
    uploaded_txt = st.file_uploader("Upload a UTF-8 .txt file", type=["txt"])
    sample_input = st.text_area(
        "Or paste text directly below:",
        height=140,
        placeholder="Paste or type text here to see Huffman Coding in action...",
    )

    text_data = None
    base_name = "compressed_output"
    if uploaded_txt is not None:
        text_data = uploaded_txt.read().decode("utf-8")
        base_name = os.path.splitext(uploaded_txt.name)[0]
    elif sample_input:
        text_data = sample_input

    if text_data is not None:
        compressed_data, stats = compress_bytes(text_data)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Original Size", f"{stats['original_size_bytes']:,} B")
        c2.metric("Compressed Size", f"{stats['compressed_size_bytes']:,} B")
        c3.metric("Space Saved", f"{stats['space_savings_pct']:.2f}%")
        c4.metric("Encoding Time", f"{stats['encoding_time_ms']:.2f} ms")

        st.download_button(
            label="⬇️ Download Compressed .huff File",
            data=compressed_data,
            file_name=f"{base_name}.huff",
            mime="application/octet-stream",
            type="primary",
        )

        st.markdown("### Generated Huffman Prefix-Free Code Table")
        code_rows = [
            {
                "Character": repr(ch),
                "Frequency": stats["freq_map"][ch],
                "Huffman Binary Code": code,
                "Bit Length": len(code),
            }
            for ch, code in sorted(
                stats["codes"].items(),
                key=lambda item: (-stats["freq_map"][item[0]], item[0]),
            )
        ]
        st.dataframe(code_rows, use_container_width=True, height=320)

with tab_decompress:
    st.subheader("Decompress a .huff File")
    uploaded_huff = st.file_uploader("Upload a .huff binary file", type=["huff"])

    if uploaded_huff is not None:
        try:
            raw_huff = uploaded_huff.read()
            restored_text, d_stats = decompress_bytes(raw_huff)

            c1, c2, c3 = st.columns(3)
            c1.metric("Compressed Input", f"{d_stats['compressed_size_bytes']:,} B")
            c2.metric("Restored Text Size", f"{d_stats['restored_size_bytes']:,} B")
            c3.metric("Decoding Time", f"{d_stats['decoding_time_ms']:.2f} ms")

            out_name = f"{os.path.splitext(uploaded_huff.name)[0]}_restored.txt"
            st.download_button(
                label="⬇️ Download Restored .txt File",
                data=restored_text.encode("utf-8"),
                file_name=out_name,
                mime="text/plain",
                type="primary",
            )

            st.markdown("### Restored Text Preview (first 2,000 characters)")
            st.text_area("Preview", restored_text[:2000], height=220, disabled=True)
        except Exception as exc:
            st.error(f"Failed to decompress file: {exc}")

with tab_benchmarks:
    st.subheader("Empirical Performance & Complexity Analysis")

    if st.button("🔄 Re-run Full Benchmark Suite"):
        with st.spinner("Running benchmarks across sample datasets..."):
            run_benchmarks()
        st.success("Benchmarks updated!")

    csv_path = os.path.join("results", "benchmark_results.csv")
    if os.path.isfile(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        st.dataframe(rows, use_container_width=True)

    col_left, col_right = st.columns(2)
    size_img = os.path.join("results", "size_comparison.png")
    time_img = os.path.join("results", "time_complexity.png")
    if os.path.isfile(size_img):
        col_left.image(size_img, caption="Original vs. Compressed File Size", use_container_width=True)
    if os.path.isfile(time_img):
        col_right.image(time_img, caption="Empirical Linear Time Complexity O(N)", use_container_width=True)
