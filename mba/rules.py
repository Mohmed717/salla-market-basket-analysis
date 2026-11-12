"""Association rule generation on top of the Apriori output."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Sequence

from .apriori import AprioriResult, FrequentItemset

__all__ = ["AssociationRule", "RuleResult", "generate_rules"]


@dataclass(frozen=True)
class AssociationRule:
    """A single ``antecedent -> consequent`` association rule."""

    antecedent: frozenset[str]
    consequent: frozenset[str]
    support: float
    confidence: float
    lift: float
    leverage: float
    conviction: float
    count: int
    antecedent_support: float
    consequent_support: float

    @property
    def antecedent_label(self) -> str:
        return " | ".join(sorted(self.antecedent))

    @property
    def consequent_label(self) -> str:
        return " | ".join(sorted(self.consequent))

    @property
    def label(self) -> str:
        return f"{self.antecedent_label}  →  {self.consequent_label}"

    def as_row(self) -> dict:
        return {
            "antecedent": self.antecedent_label,
            "consequent": self.consequent_label,
            "support": self.support,
            "confidence": self.confidence,
            "lift": self.lift,
            "leverage": self.leverage,
            "conviction": self.conviction,
            "count": self.count,
        }


@dataclass
class RuleResult:
    """All generated rules plus summary counters."""

    rules: list[AssociationRule]
    n_candidates: int
    n_kept: int

    @property
    def best_rule(self) -> AssociationRule | None:
        return self.rules[0] if self.rules else None


def _lift(confidence: float, consequent_support: float) -> float:
    if consequent_support <= 0:
        return math.inf
    return confidence / consequent_support


def _conviction(confidence: float, consequent_support: float) -> float:
    denominator = 1.0 - confidence
    numerator = 1.0 - consequent_support
    if denominator <= 0:
        return math.inf
    return numerator / denominator


def generate_rules(
    result: AprioriResult,
    min_confidence: float = 0.5,
    min_lift: float = 1.0,
    max_rules: int = 2_000,
) -> RuleResult:
    """Derive association rules from the frequent itemsets.

    Every non-empty proper subset of a frequent itemset becomes a candidate
    antecedent; the remainder is the consequent. Rules are filtered by
    confidence and lift, then sorted by lift (descending) and confidence.
    """
    if not 0.0 <= min_confidence <= 1.0:
        raise ValueError("min_confidence must be between 0 and 1")

    supports = result.supports
    rules: list[AssociationRule] = []
    candidates = 0

    for itemset in result.itemsets:
        if itemset.size < 2:
            continue
        items = sorted(itemset.items)
        pair_support = itemset.support
        count = itemset.count
        for size in range(1, len(items)):
            for combo in combinations(items, size):
                antecedent = frozenset(combo)
                consequent = frozenset(items) - antecedent
                if not consequent:
                    continue
                candidates += 1

                antecedent_support = supports.get(antecedent)
                consequent_support = supports.get(consequent)
                if antecedent_support is None or consequent_support is None:
                    continue

                confidence = pair_support / antecedent_support
                if confidence < min_confidence:
                    continue
                lift = _lift(confidence, consequent_support)
                if lift < min_lift:
                    continue

                leverage = pair_support - antecedent_support * consequent_support
                conviction = _conviction(confidence, consequent_support)

                rules.append(
                    AssociationRule(
                        antecedent=antecedent,
                        consequent=consequent,
                        support=pair_support,
                        confidence=confidence,
                        lift=lift,
                        leverage=leverage,
                        conviction=conviction,
                        count=count,
                        antecedent_support=antecedent_support,
                        consequent_support=consequent_support,
                    )
                )

    rules.sort(
        key=lambda r: (
            -r.lift,
            -r.confidence,
            -r.support,
            r.antecedent_label,
            r.consequent_label,
        )
    )
    trimmed = rules[:max_rules]
    return RuleResult(rules=trimmed, n_candidates=candidates, n_kept=len(trimmed))
