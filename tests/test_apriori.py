"""Correctness tests for the Apriori implementation and rule generation."""

from __future__ import annotations

import itertools

import pytest

from mba.apriori import apriori, transaction_itemsets
from mba.rules import generate_rules

# Classic hand-checked dataset.
# T1 {a,b,c}  T2 {a,b}  T3 {a,c}  T4 {b,c}  T5 {a,b,c}
BASKETS = [
    ["a", "b", "c"],
    ["a", "b"],
    ["a", "c"],
    ["b", "c"],
    ["a", "b", "c"],
]


def brute_force_frequent(baskets, min_support, max_len=None):
    """Reference implementation by exhaustive enumeration."""
    universe = sorted({i for b in baskets for i in b})
    n = len(baskets)
    out = {}
    limit = len(universe) if max_len is None else max_len
    for size in range(1, limit + 1):
        for combo in itertools.combinations(universe, size):
            cnt = sum(1 for b in baskets if set(combo) <= set(b))
            if cnt / n >= min_support:
                out[frozenset(combo)] = cnt
    return out


@pytest.mark.parametrize("min_support", [0.2, 0.4, 0.6, 0.8, 1.0])
def test_apriori_matches_brute_force(min_support):
    result = apriori(BASKETS, min_support=min_support, max_len=3)
    expected = brute_force_frequent(BASKETS, min_support)
    assert set(result.counts) == set(expected)
    for itemset, count in expected.items():
        assert result.counts[itemset] == count
        assert result.supports[itemset] == pytest.approx(count / len(BASKETS))


def test_known_support_values():
    result = apriori(BASKETS, min_support=0.4, max_len=3)
    assert result.counts[frozenset({"a"})] == 4
    assert result.counts[frozenset({"a", "b"})] == 3
    assert result.counts[frozenset({"a", "b", "c"})] == 2
    assert result.supports[frozenset({"a", "b"})] == pytest.approx(0.6)
    assert result.n_transactions == 5


def test_min_support_boundary_uses_ceiling():
    # 0.3 * 5 = 1.5 -> needs 2 transactions
    result = apriori(BASKETS, min_support=0.3, max_len=3)
    assert result.min_count == 2
    assert frozenset({"a"}) in result.counts

    # 0.2 * 5 = 1.0 -> 1 transaction is enough
    result = apriori(BASKETS, min_support=0.2, max_len=3)
    assert result.min_count == 1


def test_apriori_property_holds():
    """Every subset of a frequent itemset must itself be frequent."""
    result = apriori(BASKETS, min_support=0.4, max_len=3)
    for itemset in result.itemsets:
        for size in range(1, itemset.size):
            for subset in itertools.combinations(sorted(itemset.items), size):
                assert frozenset(subset) in result.counts


def test_pruning_rejects_non_frequent_candidates():
    # "a" and "d" never co-occur; {a,d} must never be produced.
    baskets = [["a", "b"], ["c", "d"], ["a", "b"], ["c", "d"]]
    result = apriori(baskets, min_support=0.25, max_len=3)
    assert frozenset({"a", "d"}) not in result.counts
    assert frozenset({"a", "b"}) in result.counts
    assert frozenset({"c", "d"}) in result.counts


def test_max_len_limits_itemset_size():
    result = apriori(BASKETS, min_support=0.2, max_len=2)
    assert all(itemset.size <= 2 for itemset in result.itemsets)
    result = apriori(BASKETS, min_support=0.2, max_len=1)
    assert all(itemset.size == 1 for itemset in result.itemsets)


def test_empty_input_is_handled():
    result = apriori([], min_support=0.1)
    assert result.empty
    assert result.itemsets == []


def test_transactions_deduplicate_items():
    baskets = transaction_itemsets([["a", "a", "b", "b"], ["a"]])
    assert baskets == [frozenset({"a", "b"}), frozenset({"a"})]


def test_rules_confidence_and_lift():
    result = apriori(BASKETS, min_support=0.4, max_len=3)
    rule_result = generate_rules(result, min_confidence=0.0, min_lift=0.0)
    by_label = {r.label: r for r in rule_result.rules}

    # a -> b : support 3/5, confidence 3/4 = 0.75, lift 0.75/0.8 = 0.9375
    rule = by_label["a  →  b"]
    assert rule.support == pytest.approx(0.6)
    assert rule.confidence == pytest.approx(0.75)
    assert rule.lift == pytest.approx(0.9375)
    assert rule.leverage == pytest.approx(0.6 - 0.8 * 0.8)

    # {a,b} -> c : support 2/5, confidence 2/3
    rule = by_label["a | b  →  c"]
    assert rule.support == pytest.approx(0.4)
    assert rule.confidence == pytest.approx(2 / 3)
    assert rule.lift == pytest.approx((2 / 3) / 0.8)


def test_rule_filtering():
    result = apriori(BASKETS, min_support=0.4, max_len=3)
    strict = generate_rules(result, min_confidence=0.9, min_lift=0.0)
    assert all(r.confidence >= 0.9 for r in strict.rules)
    assert len(strict.rules) < len(generate_rules(result, min_confidence=0.0, min_lift=0.0).rules)

    high_lift = generate_rules(result, min_confidence=0.0, min_lift=1.5)
    assert all(r.lift >= 1.5 for r in high_lift.rules)


def test_rule_candidate_count():
    result = apriori(BASKETS, min_support=0.4, max_len=3)
    rule_result = generate_rules(result, min_confidence=0.0, min_lift=0.0)
    # {a,b},{a,c},{b,c} -> 2 single antecedents each = 6
    # {a,b,c} -> 3 single + 3 pair antecedents = 6
    assert rule_result.n_candidates == 6 + 6


def test_rules_sorted_by_lift_descending():
    result = apriori(BASKETS, min_support=0.4, max_len=3)
    rules = generate_rules(result, min_confidence=0.0, min_lift=0.0).rules
    lifts = [r.lift for r in rules]
    assert lifts == sorted(lifts, reverse=True)


def test_random_datasets_match_brute_force():
    import random

    rng = random.Random(7)
    universe = [f"i{k}" for k in range(8)]
    for _ in range(12):
        baskets = []
        for _ in range(40):
            size = rng.randint(1, 5)
            baskets.append(rng.sample(universe, size))
        for min_support in (0.05, 0.1, 0.25):
            result = apriori(baskets, min_support=min_support, max_len=4)
            expected = brute_force_frequent(baskets, min_support, max_len=4)
            assert set(result.counts) == set(expected)
