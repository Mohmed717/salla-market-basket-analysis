"""CSV ingestion for market basket analysis.

Three transaction layouts are supported and auto-detected:

``basket``
    One row per transaction. Items may be packed into a single cell
    (``"a, b, c"``) or spread across several columns.
``long``
    One row per item occurrence with a transaction id column
    (``T1``/``bread`` rows).
``wide``
    One row per transaction, one column per item holding 0/1 flags.

Item names containing spaces (``"حليب طازج"``) are preserved: whitespace is
only treated as a separator when the column clearly behaves like a
space-delimited basket. The decision can always be overridden from the UI.
"""

from __future__ import annotations

import csv
import io
import os
import re
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Sequence

__all__ = [
    "TransactionDataset",
    "load_csv",
    "load_bytes",
    "detect_format",
    "split_cell",
    "DELIMITERS",
]

DELIMITERS = [",", ";", "|", "\t"]

# Explicit separators always split items.
_EXPLICIT_SPLIT_RE = re.compile(r"[,;|\n\r\t]+")
_WHITESPACE_RE = re.compile(r"\s+")

_ID_HINTS = {
    "transaction_id",
    "transactionid",
    "transaction",
    "trans_id",
    "trx_id",
    "order_id",
    "orderid",
    "order",
    "receipt",
    "receipt_id",
    "invoice",
    "invoice_id",
    "invoice_no",
    "basket_id",
    "basketid",
    "cart_id",
    "session_id",
    "visit_id",
    "customer_id",
    "cust_id",
    "id",
    "no",
    "num",
    "number",
}
_ITEM_HINTS = {
    "item",
    "items",
    "item_name",
    "itemname",
    "product",
    "product_name",
    "products",
    "sku",
    "article",
    "goods",
    "description",
    "desc",
    "basket",
    "basket_items",
    "contents",
    "items_bought",
}
_COUNT_HINTS = {"qty", "quantity", "count", "units", "amount", "price", "value", "total"}
_DATE_HINTS = {"date", "day", "time", "timestamp", "datetime", "month", "year", "week"}

_MAX_TOKENS_PER_PIECE = 12


@dataclass
class TransactionDataset:
    """Transactions extracted from a source file."""

    transactions: list[frozenset[str]] = field(default_factory=list)
    transaction_ids: list[str] = field(default_factory=list)
    format: str = "basket"
    source_name: str = ""
    columns: list[str] = field(default_factory=list)
    item_column: str | None = None
    id_column: str | None = None
    delimiter: str = ","
    n_rows: int = 0
    warnings: list[str] = field(default_factory=list)
    item_counts: Counter = field(default_factory=Counter)
    space_split: bool = False

    @property
    def n_transactions(self) -> int:
        return len(self.transactions)

    @property
    def n_items(self) -> int:
        return len(self.item_counts)

    @property
    def items(self) -> list[str]:
        return list(self.item_counts.keys())

    @property
    def basket_sizes(self) -> list[int]:
        return [len(t) for t in self.transactions]

    @property
    def avg_basket_size(self) -> float:
        if not self.transactions:
            return 0.0
        return sum(len(t) for t in self.transactions) / len(self.transactions)

    def summary(self) -> dict:
        sizes = sorted(self.basket_sizes)
        return {
            "source": self.source_name,
            "format": self.format,
            "rows": self.n_rows,
            "transactions": self.n_transactions,
            "distinct_items": self.n_items,
            "avg_basket": round(self.avg_basket_size, 2),
            "median_basket": sizes[len(sizes) // 2] if sizes else 0,
            "min_basket": min(sizes) if sizes else 0,
            "max_basket": max(sizes) if sizes else 0,
        }


def _sniff_delimiter(text: str) -> str:
    sample = text[:8000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(DELIMITERS))
        return dialect.delimiter
    except csv.Error:
        counts = {d: sample.count(d) for d in DELIMITERS}
        best = max(counts, key=lambda d: counts[d])
        return best if counts[best] > 0 else ","


def _clean(value: str) -> str:
    return value.strip().strip('"').strip()


def _normalise_key(name: str) -> str:
    return re.sub(r"[\s_\-]+", "", name.strip().lower())


def _is_item_column(name: str) -> bool:
    key = _normalise_key(name)
    if key in {_normalise_key(h) for h in _ITEM_HINTS}:
        return True
    return key.startswith("item") or key.startswith("product")


def _is_id_column(name: str) -> bool:
    key = _normalise_key(name)
    return key in {_normalise_key(h) for h in _ID_HINTS}


def _is_metadata_column(name: str) -> bool:
    key = _normalise_key(name)
    if key in {_normalise_key(h) for h in _COUNT_HINTS}:
        return True
    if key in {_normalise_key(h) for h in _DATE_HINTS}:
        return True
    return False


def _flag_ratio(rows: Sequence[Sequence[str]], col: int) -> float:
    """Share of cells in a column that behave like 0/1 flags."""
    total = 0
    flags = 0
    for row in rows:
        if col >= len(row):
            continue
        cell = row[col].strip().lower()
        if not cell:
            continue
        total += 1
        if cell in {"0", "1", "true", "false", "yes", "no", "x", "y"}:
            flags += 1
            continue
        try:
            if float(cell) in (0.0, 1.0):
                flags += 1
        except ValueError:
            pass
    return flags / total if total else 0.0


def _numeric_ratio(rows: Sequence[Sequence[str]], col: int) -> float:
    total = 0
    numeric = 0
    for row in rows:
        if col >= len(row):
            continue
        cell = row[col].strip()
        if not cell:
            continue
        total += 1
        try:
            float(cell)
            numeric += 1
        except ValueError:
            pass
    return numeric / total if total else 0.0


def split_cell(cell: str) -> list[str]:
    """Split on explicit separators only (never on spaces)."""
    return [piece.strip() for piece in _EXPLICIT_SPLIT_RE.split(cell) if piece.strip()]


def _looks_space_delimited(pieces: Sequence[str]) -> bool:
    """Decide whether a column lists items separated by spaces.

    Evidence required (all must hold):
      * cells contain several whitespace tokens on average;
      * some token recurs across different cells (a shared vocabulary);
      * no common "modifier prefix" pattern, which instead signals
        multi-word product names such as "حليب طازج" / "حليب مبستر".
    """
    if len(pieces) < 2:
        return False

    token_lists = [[t for t in _WHITESPACE_RE.split(p) if t] for p in pieces]
    token_lists = [toks for toks in token_lists if toks]
    if len(token_lists) < 2:
        return False

    avg_tokens = sum(len(t) for t in token_lists) / len(token_lists)
    if avg_tokens < 2.5:
        return False

    token_cells: dict[str, set[int]] = defaultdict(set)
    for idx, toks in enumerate(token_lists):
        for token in toks:
            token_cells[token].add(idx)
    if not any(len(cells) > 1 for cells in token_cells.values()):
        return False

    # A single dominant first token followed by mostly unique rest tokens is
    # the signature of multi-word product names, not a space-delimited list.
    first_tokens = [toks[0] for toks in token_lists]
    modal = Counter(first_tokens).most_common(1)[0]
    if modal[1] >= 0.6 * len(first_tokens):
        rest = [t for toks in token_lists for t in toks[1:]]
        if rest and len(set(rest)) / len(rest) >= 0.8:
            return False

    longest = max(len(t) for t in token_lists)
    return longest <= _MAX_TOKENS_PER_PIECE


def detect_format(
    header: Sequence[str], rows: Sequence[Sequence[str]], delimiter: str = ","
) -> str:
    """Guess the transaction layout of the parsed CSV."""
    if not rows:
        return "basket"

    n_cols = len(header)
    id_idx = next((i for i, h in enumerate(header) if _is_id_column(h)), None)
    item_idx = next((i for i, h in enumerate(header) if _is_item_column(h)), None)

    # Long format: a transaction id column plus an item column.
    if id_idx is not None and item_idx is not None and id_idx != item_idx:
        id_values = [r[id_idx] if id_idx < len(r) else "" for r in rows]
        item_values = [r[item_idx] if item_idx < len(r) else "" for r in rows]
        if (
            len(set(id_values)) < len(set(item_values))
            and len(set(id_values)) < len(id_values)
        ):
            return "long"

    # Wide format: every non-id column holds 0/1 flags.
    item_cols = [c for c in range(n_cols) if c != id_idx]
    if len(item_cols) >= 2:
        ratios = [_flag_ratio(rows, c) for c in item_cols]
        if all(r >= 0.8 for r in ratios):
            return "wide"

    # Basket format: a cell that packs several items together.
    for row in rows[:80]:
        for cell in row:
            if len(split_cell(cell)) > 1:
                return "basket"

    if id_idx is not None and item_idx is not None:
        return "long"
    return "basket"


def _parse_header(text: str) -> tuple[list[str], list[list[str]], str]:
    delimiter = _sniff_delimiter(text)
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    raw_rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not raw_rows:
        return [], [], delimiter

    first = raw_rows[0]
    # A header row carries only non-numeric labels.
    numeric_first = any(_is_number(cell) for cell in first if cell.strip())
    has_header = (
        any(cell.strip() for cell in first)
        and not numeric_first
    )
    if has_header:
        header = [_clean(c) or f"col_{i}" for i, c in enumerate(first)]
        body = raw_rows[1:]
    else:
        header = [f"col_{i}" for i in range(len(first))]
        body = raw_rows
    width = len(header)
    body = [(row + [""] * width)[:width] for row in body]
    return header, body, delimiter


def _is_number(cell: str) -> bool:
    try:
        float(cell.strip())
        return True
    except ValueError:
        return False


def _pick_item_column(
    header: Sequence[str], rows: Sequence[Sequence[str]], id_idx: int | None
) -> int | None:
    """Choose the column that holds the item names for basket files."""
    item_idx = next((i for i, h in enumerate(header) if _is_item_column(h)), None)
    if item_idx is not None:
        return item_idx

    best_col, best_score = None, -1.0
    for cidx in range(len(header)):
        if cidx == id_idx or _is_metadata_column(header[cidx]):
            continue
        cells = [r[cidx] for r in rows if cidx < len(r) and r[cidx].strip()]
        if not cells:
            continue
        pieces = sum(len(split_cell(c)) for c in cells)
        distinct = len(set(cells))
        score = pieces + distinct
        if _numeric_ratio(rows, cidx) >= 0.95 and distinct > len(cells) * 0.9:
            score -= distinct * 2
        if score > best_score:
            best_col, best_score = cidx, score
    return best_col


def load_bytes(
    data: bytes,
    source_name: str = "upload.csv",
    encoding: str = "utf-8",
) -> TransactionDataset:
    """Parse CSV bytes into a :class:`TransactionDataset`."""
    text = data.decode(encoding, errors="replace")
    if text.startswith("\ufeff"):
        text = text[1:]
    header, rows, delimiter = _parse_header(text)
    if not header:
        return TransactionDataset(
            source_name=source_name,
            warnings=["الملف فارغ أو غير قابل للقراءة."],
        )

    fmt = detect_format(header, rows, delimiter)
    warnings: list[str] = []
    id_column: str | None = None
    item_column: str | None = None
    transactions: list[frozenset[str]] = []
    transaction_ids: list[str] = []
    space_split = False

    if fmt == "long":
        id_idx = next((i for i, h in enumerate(header) if _is_id_column(h)), None)
        item_idx = next((i for i, h in enumerate(header) if _is_item_column(h)), None)
        if id_idx is None or item_idx is None:
            id_idx, item_idx = 0, 1 if len(header) > 1 else 0
        id_column = header[id_idx]
        item_column = header[item_idx]

        grouped: "OrderedDict[str, set[str]]" = OrderedDict()
        for rno, row in enumerate(rows, start=2):
            tid = _clean(row[id_idx]) if id_idx < len(row) else ""
            item = _clean(row[item_idx]) if item_idx < len(row) else ""
            if not item:
                continue
            if not tid:
                tid = f"row_{rno}"
            grouped.setdefault(tid, set()).add(item)
        transactions = [frozenset(v) for v in grouped.values()]
        transaction_ids = list(grouped.keys())

    elif fmt == "wide":
        id_idx = 0
        id_column = header[0]
        item_headers = header[1:]
        for rno, row in enumerate(rows, start=2):
            tid = _clean(row[id_idx]) if id_idx < len(row) else ""
            if not tid:
                tid = f"row_{rno}"
            items = set()
            for cidx, cell in enumerate(row[1:]):
                if cidx >= len(item_headers):
                    break
                raw = cell.strip().lower()
                if raw in {"", "0", "false", "no", "n"}:
                    continue
                items.add(item_headers[cidx])
            transactions.append(frozenset(items))
            transaction_ids.append(tid)

    else:  # basket
        id_idx = next((i for i, h in enumerate(header) if _is_id_column(h)), None)
        item_idx = _pick_item_column(header, rows, id_idx)
        if item_idx is None:
            warnings.append(
                "تعذّر تحديد عمود المنتجات. تأكد من وجود عمود يحتوي على أسماء المنتجات."
            )
        else:
            item_column = header[item_idx]
            if id_idx is None or id_idx == item_idx:
                id_idx = None
            else:
                id_column = header[id_idx]

            pieces_per_row: list[list[str]] = []
            all_pieces: list[str] = []
            for row in rows:
                raw = row[item_idx] if item_idx < len(row) else ""
                pieces = split_cell(raw)
                pieces_per_row.append(pieces)
                all_pieces.extend(pieces)
            space_split = _looks_space_delimited(all_pieces)
            if space_split:
                expanded = []
                for pieces in pieces_per_row:
                    tokens: list[str] = []
                    for piece in pieces:
                        tokens.extend(t for t in _WHITESPACE_RE.split(piece) if t)
                    expanded.append(tokens)
                pieces_per_row = expanded

            for rno, (pieces, row) in enumerate(zip(pieces_per_row, rows), start=2):
                items = {p for p in pieces if p}
                if not items:
                    continue
                tid = ""
                if id_idx is not None and id_idx < len(row):
                    tid = _clean(row[id_idx])
                if not tid:
                    tid = f"T{rno - 1}"
                transactions.append(frozenset(items))
                transaction_ids.append(tid)

    item_counts: Counter = Counter()
    for basket in transactions:
        item_counts.update(basket)

    if not transactions:
        warnings.append("لم يتم العثور على أي معاملة صالحة في الملف.")

    return TransactionDataset(
        transactions=transactions,
        transaction_ids=transaction_ids,
        format=fmt,
        source_name=source_name,
        columns=header,
        item_column=item_column,
        id_column=id_column,
        delimiter=delimiter,
        n_rows=len(rows),
        warnings=warnings,
        item_counts=item_counts,
        space_split=space_split,
    )


def load_csv(path: str | os.PathLike[str], encoding: str = "utf-8") -> TransactionDataset:
    """Load a CSV file from disk."""
    with open(path, "rb") as fh:
        data = fh.read()
    return load_bytes(data, source_name=os.path.basename(str(path)), encoding=encoding)
