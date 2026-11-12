"""Shared pytest fixtures.

The GUI tests run against Qt's offscreen platform so they work on a headless
machine.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Qt's offscreen plugin needs no display, which is what CI runners have.
# Windows runners expose a real window station, so the native plugin is used
# there instead (the offscreen build is not available on every wheel).
if sys.platform.startswith("linux"):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def qapp():
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    yield app


@pytest.fixture(scope="session")
def sample_csv() -> Path:
    path = ROOT / "data" / "sample_transactions.csv"
    if not path.exists():
        pytest.skip("sample data not generated")
    return path
