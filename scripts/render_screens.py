#!/usr/bin/env python3
"""Offscreen render harness: captures every screen of the app to PNG.

    python3 scripts/render_screens.py --out renders/

Used to visually verify the interface without a display server.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from app.main_window import MainWindow

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample_transactions.csv"


def pump(app: QApplication, rounds: int = 6) -> None:
    for _ in range(rounds):
        app.processEvents()


def capture(window: MainWindow, app: QApplication, path: Path) -> None:
    pump(app)
    path.parent.mkdir(parents=True, exist_ok=True)
    window.grab().save(str(path))
    print(f"  saved {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="renders")
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=900)
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    window = MainWindow()
    window.resize(args.width, args.height)
    window.show()
    pump(app)

    out = Path(args.out)
    capture(window, app, out / "01_home.png")

    # Load the sample dataset and run a full analysis.
    if SAMPLE.exists():
        window.controller.load_file(str(SAMPLE))
        pump(app)
        window.navigate("data")
        capture(window, app, out / "02_data.png")

        window.navigate("analysis")
        capture(window, app, out / "03_analysis.png")

        window.controller.run_analysis()
        for _ in range(200):
            app.processEvents()
            if window.controller.state.has_results:
                break
        pump(app)
        capture(window, app, out / "04_analysis_done.png")

        window.navigate("results")
        capture(window, app, out / "05_results_itemsets.png")

        tabs = window.pages["results"].tabs
        tabs.setCurrentIndex(1)
        capture(window, app, out / "06_results_rules.png")
        tabs.setCurrentIndex(2)
        capture(window, app, out / "07_results_charts.png")
        tabs.setCurrentIndex(3)
        capture(window, app, out / "08_results_summary.png")

        window.navigate("export")
        capture(window, app, out / "09_export.png")

    window.navigate("about")
    capture(window, app, out / "10_about.png")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
