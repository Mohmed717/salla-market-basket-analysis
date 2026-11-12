"""Brand identity for the Salla market basket analysis desktop app.

Everything visual - palette, typography, the logo mark and the icon set - is
defined here so the identity stays consistent across every screen.
"""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontDatabase,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)

# --------------------------------------------------------------------------
# Palette
# --------------------------------------------------------------------------
NAVY_DEEP = "#0A1526"
NAVY = "#0F1E38"
NAVY_SOFT = "#16294A"
NAVY_LINE = "#1E3357"

PRIMARY = "#2563EB"
PRIMARY_HOVER = "#1D4ED8"
PRIMARY_PRESSED = "#1E40AF"
PRIMARY_SOFT = "#EFF6FF"
PRIMARY_BORDER = "#BFDBFE"

BG = "#EDF1F7"
CARD = "#FFFFFF"
BORDER = "#E2E8F0"
BORDER_STRONG = "#CBD5E1"

TEXT = "#0F172A"
TEXT_SOFT = "#334155"
MUTED = "#64748B"
MUTED_LIGHT = "#94A3B8"

SIDEBAR_TEXT = "#94A3B8"
SIDEBAR_TEXT_ACTIVE = "#FFFFFF"

GREEN = "#16A34A"
GREEN_SOFT = "#DCFCE7"
AMBER = "#F59E0B"
AMBER_SOFT = "#FEF3C7"
TEAL = "#0EA5E9"
PURPLE = "#8B5CF6"
ROSE = "#F43F5E"

CHART_SERIES = [
    "#2563EB",
    "#10B981",
    "#F59E0B",
    "#8B5CF6",
    "#0EA5E9",
    "#F43F5E",
    "#14B8A6",
    "#EC4899",
]

# --------------------------------------------------------------------------
# Typography
# --------------------------------------------------------------------------
FONT_FAMILY = "Vazirmatn"
FONT_FALLBACK = "Noto Sans Arabic"


def available_family() -> str:
    """Return the best available Arabic-capable family."""
    families = set(QFontDatabase.families())
    for name in (FONT_FAMILY, FONT_FALLBACK, "DejaVu Sans"):
        if name in families:
            return name
    return QFont().defaultFamily()


def font(size: int = 14, weight: int = QFont.Weight.Normal, family: str | None = None) -> QFont:
    f = QFont(family or available_family())
    f.setPixelSize(size)
    f.setWeight(QFont.Weight(weight))
    f.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    return f


# --------------------------------------------------------------------------
# Icon painting
# --------------------------------------------------------------------------
def _stroke(painter: QPainter, color: str, width: float) -> None:
    pen = QPen(QColor(color))
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)


def paint_icon(painter: QPainter, name: str, rect: QRectF, color: str, width: float = 1.8) -> None:
    """Draw a line-style icon inside ``rect``."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
    s = min(w, h)
    _stroke(painter, color, width)

    if name == "home":
        path = QPainterPath()
        path.moveTo(x, y + h * 0.46)
        path.lineTo(x + w / 2, y)
        path.lineTo(x + w, y + h * 0.46)
        path.lineTo(x + w, y + h)
        path.lineTo(x + w * 0.36, y + h)
        path.lineTo(x + w * 0.36, y + h * 0.66)
        path.lineTo(x + w * 0.64, y + h * 0.66)
        path.lineTo(x + w * 0.64, y + h)
        path.lineTo(x, y + h)
        path.closeSubpath()
        painter.drawPath(path)

    elif name == "data":
        top = QRectF(x, y, w, h * 0.26)
        painter.drawArc(top, 0, 180 * 16)
        painter.drawLine(QPointF(x, y + h * 0.13), QPointF(x, y + h * 0.87))
        painter.drawLine(QPointF(x + w, y + h * 0.13), QPointF(x + w, y + h * 0.87))
        painter.drawArc(QRectF(x, y + h * 0.37, w, h * 0.26), 180 * 16, 180 * 16)
        painter.drawArc(QRectF(x, y + h * 0.61, w, h * 0.26), 180 * 16, 180 * 16)

    elif name == "analysis":
        painter.drawLine(QPointF(x, y + h), QPointF(x + w, y + h))
        for i, ratio in enumerate((0.38, 0.68, 1.0)):
            bw = w / 5
            bx = x + w * 0.12 + i * bw * 1.6
            painter.drawLine(QPointF(bx, y + h), QPointF(bx, y + h - h * ratio * 0.72))

    elif name == "results":
        painter.drawRect(QRectF(x, y, w, h))
        painter.drawLine(QPointF(x, y + h * 0.3), QPointF(x + w, y + h * 0.3))
        painter.drawLine(QPointF(x + w * 0.34, y + h * 0.3), QPointF(x + w * 0.34, y + h))
        painter.drawLine(QPointF(x + w * 0.67, y + h * 0.3), QPointF(x + w * 0.67, y + h))
        painter.drawLine(QPointF(x, y + h * 0.65), QPointF(x + w, y + h * 0.65))

    elif name == "export":
        painter.drawLine(QPointF(x + w / 2, y), QPointF(x + w / 2, y + h * 0.62))
        painter.drawLine(QPointF(x + w * 0.28, y + h * 0.4), QPointF(x + w / 2, y + h * 0.64))
        painter.drawLine(QPointF(x + w * 0.72, y + h * 0.4), QPointF(x + w / 2, y + h * 0.64))
        tray = QPainterPath()
        tray.moveTo(x, y + h * 0.62)
        tray.lineTo(x, y + h)
        tray.lineTo(x + w, y + h)
        tray.lineTo(x + w, y + h * 0.62)
        painter.drawPath(tray)

    elif name == "about":
        painter.drawEllipse(rect)
        painter.drawLine(QPointF(x + w / 2, y + h * 0.44), QPointF(x + w / 2, y + h * 0.7))
        painter.drawPoint(QPointF(x + w / 2, y + h * 0.32))

    elif name == "folder":
        shape = QPainterPath()
        shape.moveTo(x, y + h * 0.2)
        shape.lineTo(x + w * 0.38, y + h * 0.2)
        shape.lineTo(x + w * 0.5, y + h * 0.38)
        shape.lineTo(x + w, y + h * 0.38)
        shape.lineTo(x + w, y + h * 0.86)
        shape.lineTo(x, y + h * 0.86)
        shape.closeSubpath()
        painter.drawPath(shape)

    elif name == "play":
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(x + w * 0.26, y + h * 0.16),
                    QPointF(x + w * 0.82, y + h / 2),
                    QPointF(x + w * 0.26, y + h * 0.84),
                ]
            )
        )

    elif name == "bulb":
        painter.drawEllipse(QRectF(x + w * 0.24, y, w * 0.52, h * 0.6))
        painter.drawLine(QPointF(x + w * 0.38, y + h * 0.72), QPointF(x + w * 0.62, y + h * 0.72))
        painter.drawLine(QPointF(x + w * 0.42, y + h * 0.86), QPointF(x + w * 0.58, y + h * 0.86))

    elif name == "check":
        painter.drawPolyline(
            QPolygonF(
                [
                    QPointF(x + w * 0.14, y + h * 0.52),
                    QPointF(x + w * 0.4, y + h * 0.78),
                    QPointF(x + w * 0.86, y + h * 0.24),
                ]
            )
        )

    elif name == "refresh":
        painter.drawArc(QRectF(x + w * 0.08, y + h * 0.08, w * 0.84, h * 0.84), 40 * 16, 280 * 16)
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(x + w * 0.58, y + h * 0.02),
                    QPointF(x + w * 0.86, y + h * 0.28),
                    QPointF(x + w * 0.54, y + h * 0.4),
                ]
            )
        )

    elif name == "cart":
        painter.drawPath(
            QPainterPath()
            .moveTo(x + w * 0.02, y + h * 0.12)
            .lineTo(x + w * 0.22, y + h * 0.12)
            .lineTo(x + w * 0.34, y + h * 0.74)
            .lineTo(x + w * 0.86, y + h * 0.74)
            .lineTo(x + w * 0.98, y + h * 0.3)
            .lineTo(x + w * 0.16, y + h * 0.3)
        )
        painter.drawEllipse(QRectF(x + w * 0.36, y + h * 0.84, w * 0.11, h * 0.11))
        painter.drawEllipse(QRectF(x + w * 0.72, y + h * 0.84, w * 0.11, h * 0.11))

    elif name == "basket_brand":
        painter.drawPath(
            QPainterPath()
            .moveTo(x + w * 0.08, y + h * 0.3)
            .lineTo(x + w * 0.92, y + h * 0.3)
            .lineTo(x + w * 0.8, y + h * 0.92)
            .lineTo(x + w * 0.2, y + h * 0.92)
            .closeSubpath()
        )
        painter.drawArc(QRectF(x + w * 0.28, y + h * 0.04, w * 0.44, h * 0.44), 0, 180 * 16)

    painter.restore()


class IconWidget:
    """Mixin helper that paints an icon inside a widget."""

    @staticmethod
    def paint(widget, name: str, color: str, width: float = 1.8, margin: float = 0.16) -> None:
        painter = QPainter(widget)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = widget.rect()
        side = min(rect.width(), rect.height())
        box = QRectF(
            rect.x() + (rect.width() - side) / 2 + side * margin,
            rect.y() + (rect.height() - side) / 2 + side * margin,
            side * (1 - 2 * margin),
            side * (1 - 2 * margin),
        )
        paint_icon(painter, name, box, color, width)
        painter.end()


def paint_logo(painter: QPainter, rect: QRectF, badge_only: bool = False) -> None:
    """Paint the Salla brand mark: a basket with data rising out of it."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    side = min(rect.width(), rect.height())
    badge = QRectF(
        rect.x() + (rect.width() - side) / 2,
        rect.y() + (rect.height() - side) / 2,
        side,
        side,
    )

    gradient = QLinearGradient(badge.topLeft(), badge.bottomRight())
    gradient.setColorAt(0.0, QColor("#3B7BFF"))
    gradient.setColorAt(0.55, QColor("#1D4ED8"))
    gradient.setColorAt(1.0, QColor("#0A1526"))
    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(badge, side * 0.27, side * 0.27)

    inner = badge.adjusted(side * 0.21, side * 0.21, -side * 0.21, -side * 0.21)

    # The basket body: a filled trapezoid holding the base of the bars.
    rim_y = inner.top() + inner.height() * 0.60
    basket = QPainterPath()
    basket.moveTo(inner.left(), rim_y)
    basket.lineTo(inner.right(), rim_y)
    basket.lineTo(inner.right() - inner.width() * 0.13, inner.bottom())
    basket.lineTo(inner.left() + inner.width() * 0.13, inner.bottom())
    basket.closeSubpath()
    painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPath(basket)

    # Rising bars: they start inside the basket and climb above the rim.
    painter.setBrush(Qt.BrushStyle.NoBrush)
    pen = QPen(QColor("#BFDBFE"))
    pen.setWidthF(side * 0.085)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    bar_width = inner.width() / 6.4
    for i, height_ratio in enumerate((0.34, 0.58, 0.86)):
        bx = inner.left() + bar_width * (0.7 + i * 1.75)
        top_y = inner.bottom() - inner.height() * height_ratio
        painter.drawLine(
            QPointF(bx + bar_width / 2, inner.bottom() - inner.height() * 0.10),
            QPointF(bx + bar_width / 2, top_y),
        )

    painter.restore()
