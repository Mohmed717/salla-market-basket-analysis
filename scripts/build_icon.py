#!/usr/bin/env python3
"""Render the brand mark into a PNG (and ICO) for the application icon.

    python3 scripts/build_icon.py [--out assets/icon.png] [--ico assets/icon.ico]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# The offscreen plugin is unavailable on some Windows builds, where the
# native platform plugin is used instead.
if sys.platform.startswith("linux") or sys.platform == "darwin":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import QApplication

from app import brand


def render(size: int) -> QPixmap:
    app = QApplication.instance() or QApplication([])
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    brand.paint_logo(painter, QRectF(0, 0, size, size))
    painter.end()
    return pixmap


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="assets/icon.png")
    parser.add_argument("--ico", default="")
    parser.add_argument("--size", type=int, default=512)
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pixmap = render(args.size)
    pixmap.save(str(out), "PNG")
    print(f"wrote {out} ({args.size}x{args.size})")

    if args.ico:
        ico = Path(args.ico)
        ico.parent.mkdir(parents=True, exist_ok=True)
        try:
            from PIL import Image

            Image.open(out).save(ico, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        except ImportError:
            # Pillow is optional; fall back to Qt's ICO writer.
            pixmap.save(str(ico), "ICO")
        print(f"wrote {ico}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
