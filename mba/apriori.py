"""Pure-Python Apriori algorithm for frequent itemset mining.

The implementation follows the classic two-phase strategy of Agrawal & Agrawal:

    L_1 = { single items with support >= min_support }
    L_k = { candidates of size k generated from L_{k-1} and pruned with the
            apriori property, whose support exceeds min_support }

No third-party mining library is used; everything here is plain Python so the
tool stays dependency-light and the algorithm stays auditable.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from typing import Iterable, Mapping, Sequence

__all__ = ["FrequentItemset", "AprioriResult", "apriori", "transaction_itemsets"]


@dataclass(frozen=True, order=True)
class FrequentItemset:
    """A frequent itemset with its support statistics."""

    items: frozenset[str]
    support: float
    count: int
    size: int = field(init=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "size", len(self.items))

    @property
    def label(self) -> str:
        """Human readable representation used by the UI and exports."""
        return " | ".join(sorted(self.items))

    def as_row(self) -> dict:
        return {
            "itemset": self.label,
            "items": sorted(self.items),
            "size": self.size,
            "support": self.support,
            "count": self.count,
        }


@dataclass
class AprioriResult:
    """Outcome of an Apriori run."""

    itemsets: list[FrequentItemset]
    supports: dict[frozenset[str], float]
    counts: dict[frozenset[str], int]
    levels: dict[int, list[FrequentItemset]]
    n_transactions: int
    min_support: float
    min_count: int
    empty: bool = False
    notes: list[str] = field(default_factory=list)

    @property
    def frequent_single_items(self) -> list[FrequentItemset]:
        return self.levels.get(1, [])


def transaction_itemsets(transactions: Iterable[Iterable[str]]) -> list[frozenset[str]]:
    """Normalise raw transaction rows into de-duplicated item sets."""
    out: list[frozenset[str]] = []
    for row in transactions:
        items = {str(item).strip() for item in row if str(item).strip()}
        if items:
            out.append(frozenset(items))
    return out


def _join(frequent_level: Sequence[frozenset[str]]) -> set[frozenset[str]]:
    """Generate the candidate set C_k from L_{k-1} (self-join on prefix)."""
    tuples = sorted(tuple(sorted(itemset)) for itemset in frequent_level)
    candidates: set[frozenset[str]] = set()
    for i in range(len(tuples)):
        left = tuples[i]
        for j in range(i + 1, len(tuples)):
            right = tuples[j]
            # The first k-2 items must be identical for the join to succeed.
            if left[:-1] != right[:-1]:
                continue
            if left[-1] == right[-1]:
                continue
            candidates.add(frozenset(left + (right[-1],)))
    return candidates


def _prune(
    candidates: Iterable[frozenset[str]], frequent_level: Iterable[frozenset[str]]
) -> set[frozenset[str]]:
    """Apply the apriori property: every (k-1)-subset must be frequent."""
    level_set = set(frequent_level)
    kept: set[frozenset[str]] = set()
    for candidate in candidates:
        ok = True
        for item in candidate:
            subset = candidate - {item}
            if subset not in level_set:
                ok = False
                break
        if ok:
            kept.add(candidate)
    return kept


def _build_postings(transactions: Sequence[frozenset[str]]) -> dict[str, set[int]]:
    """Item -> set of transaction indices containing it."""
    postings: dict[str, set[int]] = defaultdict(set)
    for idx, basket in enumerate(transactions):
        for item in basket:
            postings[item].add(idx)
    return postings


def _count_support(itemset: frozenset[str], postings: Mapping[str, set[int]]) -> int:
    """Count transactions containing every item of the itemset."""
    lists = [postings[item] for item in itemset if item in postings]
    if len(lists) != len(itemset):
        return 0
    if not lists:
        return 0
    return len(set.intersection(*lists))


def apriori(
    transactions: Iterable[Iterable[str]],
    min_support: float = 0.05,
    max_len: int = 3,
    max_itemsets: int = 500_000,
) -> AprioriResult:
    """Mine frequent itemsets.

    Parameters
    ----------
    transactions:
        Iterable of baskets; each basket is an iterable of item names.
    min_support:
        Minimum relative support in ``[0, 1]``.
    max_len:
        Maximum itemset size to mine.
    max_itemsets:
        Safety cap on the number of itemsets kept, protecting the UI from
        pathological inputs.
    """
    if not 0.0 <= min_support <= 1.0:
        raise ValueError("min_support must be between 0 and 1")
    if max_len < 1:
        raise ValueError("max_len must be >= 1")

    baskets = transaction_itemsets(transactions)
    n = len(baskets)
    if n == 0:
        return AprioriResult([], {}, {}, {}, 0, min_support, 0, empty=True)

    min_count = max(1, math.ceil(min_support * n - 1e-9))
    postings = _build_postings(baskets)

    counts: dict[frozenset[str], int] = {}
    supports: dict[frozenset[str], float] = {}
    levels: dict[int, list[FrequentItemset]] = {}
    notes: list[str] = []

    # ---- L_1 -------------------------------------------------------------
    current = [
        frozenset({item}) for item, post in postings.items() if len(post) >= min_count
    ]
    for itemset in current:
        cnt = len(postings[next(iter(itemset))])
        counts[itemset] = cnt
        supports[itemset] = cnt / n

    level_number = 1
    while current and level_number < max_len:
        if len(counts) >= max_itemsets:
            notes.append(
                f"تم إيقاف التعدين عند حد {max_itemsets:,} مجموعة عناصر لحماية الذاكرة."
            )
            break

        candidates = _prune(_join(current), current)
        next_level: list[frozenset[str]] = []
        for candidate in sorted(candidates, key=lambda s: sorted(s)):
            cnt = _count_support(candidate, postings)
            if cnt >= min_count:
                counts[candidate] = cnt
                supports[candidate] = cnt / n
                next_level.append(candidate)
            if len(counts) >= max_itemsets:
                notes.append(
                    f"تم إيقاف التعدين عند حد {max_itemsets:,} مجموعة عناصر لحماية الذاكرة."
                )
                break
        if not next_level:
            break
        level_number += 1
        current = next_level

    itemsets: list[FrequentItemset] = []
    for size, level in levels.items():  # pragma: no cover - placeholder
        itemsets.extend(level)

    # Rebuild levels in a stable order for presentation.
    levels = {}
    itemsets = []
    for itemset, cnt in counts.items():
        support = supports[itemset]
        fi = FrequentItemset(items=itemset, support=support, count=cnt)
        levels.setdefault(len(itemset), []).append(fi)
    for size in levels:
        levels[size].sort(key=lambda fi: (-fi.support, fi.label))
        itemsets.extend(levels[size])
    itemsets.sort(key=lambda fi: (-fi.support, fi.size, fi.label))

    return AprioriResult(
        itemsets=itemsets,
        supports=supports,
        counts=counts,
        levels=levels,
        n_transactions=n,
        min_support=min_support,
        min_count=min_count,
        notes=notes,
    )


def count_combinations_support(
    transactions: Sequence[frozenset[str]], itemset: Iterable[str]
) -> int:
    """Utility: number of baskets containing every item of ``itemset``."""
    wanted = set(itemset)
    return sum(1 for basket in transactions if wanted <= basket)


def all_subsets(items: Iterable[str]) -> list[frozenset[str]]:
    """All non-empty subsets of ``items`` (ordered by size then content)."""
    pool = sorted(set(items))
    out: list[frozenset[str]] = []
    for size in range(1, len(pool) + 1):
        for combo in combinations(pool, size):
            out.append(frozenset(combo))
    return out
