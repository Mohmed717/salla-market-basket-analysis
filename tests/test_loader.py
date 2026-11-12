"""Tests for CSV ingestion across the three supported transaction layouts."""

from __future__ import annotations

import io

import pytest

from mba.loader import detect_format, load_bytes

BASKET_CSV = """transaction_id,items,quantity
T1,;a;b;c,3
T2,a;b,2
T3,a;c,1
"""

LONG_CSV = """transaction_id,item
T1,حليب
T1,خبز
T2,حليب
T3,عسل
T3,خبز
"""

WIDE_CSV = """transaction_id,حليب,خبز,عسل
T1,1,1,0
T2,1,0,0
T3,0,1,1
"""

SEMICOLON_QUOTED = """id;"products"
1;"a;b;c"
2;"b;d"
"""


def test_basket_format_detected_and_parsed():
    ds = load_bytes(BASKET_CSV.encode("utf-8"), "basket.csv")
    assert ds.format == "basket"
    assert ds.n_transactions == 3
    assert ds.transaction_ids == ["T1", "T2", "T3"]
    assert ds.transactions[0] == frozenset({"a", "b", "c"})
    assert ds.transactions[1] == frozenset({"a", "b"})
    assert ds.item_column == "items"
    assert ds.id_column == "transaction_id"


def test_long_format_detected_and_grouped():
    ds = load_bytes(LONG_CSV.encode("utf-8"), "long.csv")
    assert ds.format == "long"
    assert ds.n_transactions == 3
    assert ds.transactions[0] == frozenset({"حليب", "خبز"})
    assert ds.transactions[2] == frozenset({"عسل", "خبز"})
    assert ds.item_counts["خبز"] == 2


def test_wide_format_detected_and_expanded():
    ds = load_bytes(WIDE_CSV.encode("utf-8"), "wide.csv")
    assert ds.format == "wide"
    assert ds.n_transactions == 3
    assert ds.transactions[0] == frozenset({"حليب", "خبز"})
    assert ds.transactions[2] == frozenset({"خبز", "عسل"})


def test_bom_is_stripped():
    data = "﻿" + BASKET_CSV
    ds = load_bytes(data.encode("utf-8"), "bom.csv")
    assert ds.n_transactions == 3
    assert ds.item_column == "items"


def test_quoted_delimiter_inside_cell():
    ds = load_bytes(SEMICOLON_QUOTED.encode("utf-8"), "q.csv")
    assert ds.n_transactions == 2
    assert ds.transactions[0] == frozenset({"a", "b", "c"})


def test_empty_file_returns_warning():
    ds = load_bytes(b"", "empty.csv")
    assert ds.n_transactions == 0
    assert ds.warnings


def test_header_only_file():
    ds = load_bytes(b"transaction_id,items\n", "header.csv")
    assert ds.n_transactions == 0


def test_missing_header_uses_generated_names():
    ds = load_bytes(b"1,a;b\n2,c\n", "noheader.csv")
    assert ds.n_transactions == 2
    assert ds.transactions[0] == frozenset({"a", "b"})


def test_rtl_and_arabic_items_preserved():
    csv_text = "transaction_id,products\nX1,منتج أول;منتج ثانٍ\n"
    ds = load_bytes(csv_text.encode("utf-8"), "rtl.csv")
    assert ds.transactions[0] == frozenset({"منتج أول", "منتج ثانٍ"})


def test_empty_rows_are_skipped():
    csv_text = "transaction_id,items\nX1,a;b\nX2,\nX3,c\n"
    ds = load_bytes(csv_text.encode("utf-8"), "sparse.csv")
    assert ds.n_transactions == 2


def test_summary_metrics():
    ds = load_bytes(BASKET_CSV.encode("utf-8"), "basket.csv")
    summary = ds.summary()
    assert summary["transactions"] == 3
    assert summary["distinct_items"] == 3
    assert summary["max_basket"] == 3
    assert summary["min_basket"] == 2


def test_detect_format_on_empty_rows():
    assert detect_format(["a", "b"], [], ",") == "basket"


def test_generated_sample_files_load():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "data"
    for name in ("sample_transactions.csv", "sample_long.csv", "sample_wide.csv"):
        path = root / name
        if not path.exists():
            pytest.skip(f"{name} not generated")
        with path.open("rb") as fh:
            ds = load_bytes(fh.read(), name)
        assert ds.n_transactions > 0
        assert ds.n_items > 5
