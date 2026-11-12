"""Smoke tests for the desktop application layer."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.main_window import MainWindow


@pytest.fixture()
def window(qapp):
    win = MainWindow()
    win.resize(1440, 900)
    win.show()
    qapp.processEvents()
    yield win
    win.close()


def _run_analysis(window, qapp, sample_csv) -> None:
    window.controller.load_file(str(sample_csv))
    qapp.processEvents()
    window.controller.run_analysis()
    for _ in range(400):
        qapp.processEvents()
        if window.controller.state.has_results:
            break
    qapp.processEvents()


def test_window_builds_with_all_pages(window):
    assert set(window.pages) == {"home", "data", "analysis", "results", "export", "about"}
    assert window.stack.count() == 6


def test_navigation_switches_pages(window, qapp):
    for key in ("data", "analysis", "results", "export", "about", "home"):
        window.navigate(key)
        qapp.processEvents()
        assert window.stack.currentWidget() is window.pages[key]
        assert window.sidebar.buttons[key].isChecked()


def test_load_sample_populates_dataset(window, qapp, sample_csv):
    window.controller.load_file(str(sample_csv))
    qapp.processEvents()
    state = window.controller.state
    assert state.has_data
    assert state.dataset.n_transactions == 1500
    assert state.dataset.n_items > 20
    assert state.dataset.format == "basket"


def test_analysis_populates_tables(window, qapp, sample_csv):
    _run_analysis(window, qapp, sample_csv)
    state = window.controller.state
    assert state.has_results
    assert len(state.result.itemsets) > 0
    assert len(state.rules.rules) > 0

    results = window.pages["results"]
    assert results.itemsets_table.model().rowCount() == len(state.result.itemsets)
    assert results.rules_table.model().rowCount() == len(state.rules.rules)

    analysis = window.pages["analysis"]
    assert analysis.rules_table.model().rowCount() > 0


def test_parameters_are_applied(window, qapp, sample_csv):
    window.controller.load_file(str(sample_csv))
    qapp.processEvents()
    page = window.pages["analysis"]
    page.support_spin.setValue(40)
    page.confidence_spin.setValue(90)
    qapp.processEvents()
    assert window.controller.state.min_support == pytest.approx(0.40)
    assert window.controller.state.min_confidence == pytest.approx(0.90)

    _run_analysis(window, qapp, sample_csv)
    for rule in window.controller.state.rules.rules:
        assert rule.confidence >= 0.90


def test_exports_write_csv(window, qapp, sample_csv, tmp_path):
    _run_analysis(window, qapp, sample_csv)
    itemsets_path = window.controller.export_itemsets_csv(str(tmp_path))
    rules_path = window.controller.export_rules_csv(str(tmp_path))
    transactions_path = window.controller.export_transactions_csv(str(tmp_path))

    for path in (itemsets_path, rules_path, transactions_path):
        assert path and Path(path).exists()
        with open(path, encoding="utf-8-sig") as fh:
            rows = list(csv.reader(fh))
        assert rows, "exported file should not be empty"

    with open(itemsets_path, encoding="utf-8-sig") as fh:
        header = next(csv.reader(fh))
    assert header == ["itemset", "size", "support", "count"]


def test_pages_render_without_error(window, qapp, sample_csv):
    _run_analysis(window, qapp, sample_csv)
    results = window.pages["results"]
    for index in range(results.tabs.count()):
        results.tabs.setCurrentIndex(index)
        qapp.processEvents()
    for key in window.pages:
        window.navigate(key)
        qapp.processEvents()
    assert window.grab().isNull() is False
