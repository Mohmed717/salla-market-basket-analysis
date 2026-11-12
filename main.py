#!/usr/bin/env python3
"""Launch the Salla market basket analysis desktop application."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QGuiApplication, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication

from app import brand
from app.main_window import MainWindow


def build_icon(size: int = 256) -> QIcon:
    """Render the brand mark into an application icon."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    brand.paint_logo(painter, QRectF(0, 0, size, size))
    painter.end()
    return QIcon(pixmap)


def main() -> int:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("سَلّة")
    app.setApplicationDisplayName("سَلّة — تحليل سلة المشتريات")
    app.setOrganizationName("Salla")
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setWindowIcon(build_icon())

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
