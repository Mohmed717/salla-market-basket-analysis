"""Market basket analysis: Apriori frequent itemsets and association rules."""

from .apriori import AprioriResult, FrequentItemset, apriori
from .loader import TransactionDataset, load_csv, load_bytes
from .rules import AssociationRule, RuleResult, generate_rules

__version__ = "1.0.0"

__all__ = [
    "AprioriResult",
    "FrequentItemset",
    "apriori",
    "TransactionDataset",
    "load_csv",
    "load_bytes",
    "AssociationRule",
    "RuleResult",
    "generate_rules",
    "__version__",
]
