"""Application state and the analysis pipeline, shared by every page."""

from __future__ import annotations

import csv
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from mba.apriori import AprioriResult, apriori
from mba.loader import TransactionDataset, load_bytes
from mba.rules import RuleResult, generate_rules

EXPORT_DIR = Path("exports")


@dataclass
class AnalysisState:
    """Everything the UI needs to render the current analysis."""

    dataset: TransactionDataset | None = None
    file_path: str | None = None
    result: AprioriResult | None = None
    rules: RuleResult | None = None
    min_support: float = 0.10
    min_confidence: float = 0.60
    min_lift: float = 1.0
    max_len: int = 3
    runtime: float = 0.0
    error: str = ""

    @property
    def has_data(self) -> bool:
        return self.dataset is not None and self.dataset.n_transactions > 0

    @property
    def has_results(self) -> bool:
        return self.result is not None and self.rules is not None

    def reset_results(self) -> None:
        self.result = None
        self.rules = None
        self.runtime = 0.0


class AnalysisWorker(QThread):
    """Runs Apriori off the UI thread so the window never freezes."""

    finished_ok = pyqtSignal(object, object, float)
    failed = pyqtSignal(str)

    def __init__(
        self,
        transactions,
        min_support: float,
        min_confidence: float,
        min_lift: float,
        max_len: int,
    ):
        super().__init__()
        self.transactions = transactions
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.min_lift = min_lift
        self.max_len = max_len

    def run(self) -> None:  # noqa: D102
        try:
            started = time.perf_counter()
            result = apriori(
                self.transactions,
                min_support=self.min_support,
                max_len=self.max_len,
            )
            rules = generate_rules(
                result,
                min_confidence=self.min_confidence,
                min_lift=self.min_lift,
            )
            elapsed = time.perf_counter() - started
            self.finished_ok.emit(result, rules, elapsed)
        except Exception as exc:  # pragma: no cover - defensive
            self.failed.emit(str(exc))


class Controller(QObject):
    """Mediates between the pages and the analysis engine."""

    data_changed = pyqtSignal()
    results_changed = pyqtSignal()
    status_changed = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.state = AnalysisState()
        self._worker: AnalysisWorker | None = None

    # -- data ---------------------------------------------------------------
    def load_file(self, path: str) -> bool:
        try:
            with open(path, "rb") as fh:
                payload = fh.read()
        except OSError as exc:
            self.state.error = f"تعذّر فتح الملف: {exc}"
            self.status_changed.emit(self.state.error)
            return False
        return self.load_payload(payload, os.path.basename(path), path)

    def load_payload(self, payload: bytes, name: str, path: str | None = None) -> bool:
        dataset = load_bytes(payload, source_name=name)
        self.state.dataset = dataset
        self.state.file_path = path
        self.state.reset_results()
        self.state.error = ""
        self.data_changed.emit()
        self.results_changed.emit()
        if dataset.warnings:
            self.status_changed.emit(dataset.warnings[0])
        else:
            self.status_changed.emit(
                f"تم تحميل {dataset.n_transactions:,} معاملة و {dataset.n_items:,} منتج."
            )
        return bool(dataset.n_transactions)

    # -- analysis -----------------------------------------------------------
    def run_analysis(self) -> None:
        if not self.state.has_data:
            self.status_changed.emit("الرجاء تحميل ملف بيانات أولاً.")
            return
        st = self.state
        self.status_changed.emit("جارٍ تنفيذ خوارزمية Apriori…")
        worker = AnalysisWorker(
            list(st.dataset.transactions),
            st.min_support,
            st.min_confidence,
            st.min_lift,
            st.max_len,
        )
        worker.finished_ok.connect(self._on_finished)
        worker.failed.connect(self._on_failed)
        self._worker = worker
        worker.start()

    def _on_finished(self, result: AprioriResult, rules: RuleResult, elapsed: float) -> None:
        st = self.state
        st.result = result
        st.rules = rules
        st.runtime = elapsed
        self.results_changed.emit()
        self.status_changed.emit(
            f"اكتمل التحليل في {elapsed:.2f} ثانية — "
            f"{len(result.itemsets):,} مجموعة متكررة و {len(rules.rules):,} قاعدة ارتباط."
        )

    def _on_failed(self, message: str) -> None:
        self.state.error = message
        self.status_changed.emit(f"فشل التحليل: {message}")

    # -- exports ------------------------------------------------------------
    def export_itemsets_csv(self, directory: str | None = None) -> str | None:
        st = self.state
        if not st.result:
            return None
        target = Path(directory or EXPORT_DIR)
        target.mkdir(parents=True, exist_ok=True)
        path = target / "frequent_itemsets.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(["itemset", "size", "support", "count"])
            for itemset in st.result.itemsets:
                writer.writerow([itemset.label, itemset.size, round(itemset.support, 6), itemset.count])
        return str(path)

    def export_rules_csv(self, directory: str | None = None) -> str | None:
        st = self.state
        if not st.rules:
            return None
        target = Path(directory or EXPORT_DIR)
        target.mkdir(parents=True, exist_ok=True)
        path = target / "association_rules.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                [
                    "antecedent",
                    "consequent",
                    "support",
                    "confidence",
                    "lift",
                    "leverage",
                    "conviction",
                    "count",
                ]
            )
            for rule in st.rules.rules:
                writer.writerow(
                    [
                        rule.antecedent_label,
                        rule.consequent_label,
                        round(rule.support, 6),
                        round(rule.confidence, 6),
                        round(rule.lift, 6),
                        round(rule.leverage, 6),
                        round(rule.conviction, 6),
                        rule.count,
                    ]
                )
        return str(path)

    def export_transactions_csv(self, directory: str | None = None) -> str | None:
        st = self.state
        if not st.dataset:
            return None
        target = Path(directory or EXPORT_DIR)
        target.mkdir(parents=True, exist_ok=True)
        path = target / "transactions_normalised.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(["transaction_id", "items", "item_count"])
            for tid, basket in zip(st.dataset.transaction_ids, st.dataset.transactions):
                writer.writerow([tid, "; ".join(sorted(basket)), len(basket)])
        return str(path)
