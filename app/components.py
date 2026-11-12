"""Reusable UI components for the Salla desktop application."""

from __future__ import annotations

from typing import Iterable, Sequence

from PyQt6.QtCore import QEvent, QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QGuiApplication,
    QIcon,
    QPainter,
    QPainterPath,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QFrame,
    QHeaderView,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyleOptionButton,
    QStylePainter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from . import brand


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet(f"background:{brand.BORDER};")
    return line


def vline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.VLine)
    line.setFixedWidth(1)
    line.setStyleSheet(f"background:{brand.BORDER};")
    return line


def elide(text: str, limit: int = 48) -> str:
    text = text or ""
    return text if len(text) <= limit else text[: limit - 1] + "…"


# --------------------------------------------------------------------------
# Buttons
# --------------------------------------------------------------------------
def _sort_arrow_assets() -> tuple[str, str]:
    """Create the small sort-indicator arrows used by the table header."""
    import tempfile
    from pathlib import Path

    folder = Path(tempfile.gettempdir()) / "salla_ui_assets"
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, up in (("sort_up.png", True), ("sort_down.png", False)):
        target = folder / name
        if not target.exists():
            pixmap = QPixmap(12, 12)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#93C5FD"))
            arrow = QPainterPath()
            if up:
                arrow.moveTo(6, 2.5)
                arrow.lineTo(10.5, 9)
                arrow.lineTo(1.5, 9)
            else:
                arrow.moveTo(6, 9.5)
                arrow.lineTo(1.5, 3)
                arrow.lineTo(10.5, 3)
            arrow.closeSubpath()
            painter.drawPath(arrow)
            painter.end()
            pixmap.save(str(target))
        paths.append(str(target))
    return paths[0], paths[1]


def paint_button_content(
    button: QPushButton,
    icon_name: str = "",
    icon_color: str = brand.TEXT,
    text_color: str = brand.TEXT,
    icon_size: int = 16,
    gap: int = 10,
    margin: int = 14,
) -> None:
    """Draw a button's icon and text so they never overlap.

    Qt stylesheet padding is mirrored for right-to-left widgets, so the icon
    and the label are positioned explicitly here instead.
    """
    option = QStyleOptionButton()
    button.initStyleOption(option)
    option.text = ""
    painter = QStylePainter(button)
    button.style().drawControl(QStyle.ControlElement.CE_PushButton, option, painter, button)

    rect = button.rect()
    text_right = rect.right() - margin
    if icon_name:
        icon_rect = QRectF(
            rect.right() - margin - icon_size,
            (rect.height() - icon_size) / 2.0,
            icon_size,
            icon_size,
        )
        brand.paint_icon(painter, icon_name, icon_rect, icon_color, 1.8)
        text_right = icon_rect.left() - gap

    text = button.text()
    if text:
        metrics = QFontMetrics(button.font())
        width = metrics.horizontalAdvance(text)
        text_rect = QRectF(max(rect.left(), text_right - width), 0, width, rect.height())
        painter.setPen(QColor(text_color))
        painter.drawText(
            text_rect,
            int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            text,
        )
    painter.end()


class IconButton(QPushButton):
    """A flat button with a vector icon painted on its leading edge."""

    def __init__(self, text: str = "", icon: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.icon_name = icon
        self.icon_color = brand.MUTED
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setIconSize(QSize(18, 18))
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                color: {brand.TEXT_SOFT};
                border: none;
                font-weight: 500;
            }}
            QPushButton:hover {{ color: {brand.PRIMARY}; }}
            """
        )

    def setIconColor(self, color: str) -> None:
        self.icon_color = color
        self.update()

    def paintEvent(self, event):  # noqa: N802 - Qt naming
        if not self.icon_name:
            super().paintEvent(event)
            return
        paint_button_content(
            self,
            self.icon_name,
            self.icon_color,
            brand.TEXT_SOFT,
            icon_size=17,
            margin=12,
        )


class PrimaryButton(QPushButton):
    """The main call-to-action button (solid blue)."""

    def __init__(self, text: str = "", icon: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.icon_name = icon
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(44)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 {brand.PRIMARY}, stop:1 {brand.PRIMARY_HOVER});
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-weight: 600;
                padding: 10px 22px;
            }}
            QPushButton:hover {{ background: {brand.PRIMARY_HOVER}; }}
            QPushButton:pressed {{ background: {brand.PRIMARY_PRESSED}; }}
            QPushButton:disabled {{ background: #B6C6E4; color: #EEF3FB; }}
            """
        )

    def paintEvent(self, event):  # noqa: N802
        paint_button_content(
            self,
            self.icon_name,
            "#FFFFFF",
            "#FFFFFF",
            icon_size=16,
            margin=18,
        )


class GhostButton(QPushButton):
    """A secondary button: white background, light border."""

    def __init__(self, text: str = "", icon: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.icon_name = icon
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(38)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: {brand.CARD};
                color: {brand.TEXT_SOFT};
                border: 1px solid {brand.BORDER_STRONG};
                border-radius: 9px;
                padding: 7px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{ border-color: {brand.PRIMARY}; color: {brand.PRIMARY}; }}
            QPushButton:pressed {{ background: {brand.PRIMARY_SOFT}; }}
            QPushButton:disabled {{ color: {brand.MUTED_LIGHT}; background: #F8FAFC; }}
            """
        )

    def paintEvent(self, event):  # noqa: N802
        paint_button_content(
            self,
            self.icon_name,
            brand.MUTED,
            brand.TEXT_SOFT,
            icon_size=15,
            margin=16,
        )


# --------------------------------------------------------------------------
# Cards
# --------------------------------------------------------------------------
class Card(QFrame):
    """White rounded card with a soft shadow."""

    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        parent: QWidget | None = None,
        shadow: bool = True,
    ):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setStyleSheet(
            f"""
            QFrame#Card {{
                background: {brand.CARD};
                border: 1px solid {brand.BORDER};
                border-radius: 14px;
            }}
            """
        )
        if shadow:
            effect = QGraphicsDropShadowEffect(self)
            effect.setBlurRadius(26)
            effect.setXOffset(0)
            effect.setYOffset(4)
            effect.setColor(QColor(15, 30, 56, 38))
            self.setGraphicsEffect(effect)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(18, 16, 18, 18)
        self._outer.setSpacing(12)

        self.header: QHBoxLayout | None = None
        self.body: QVBoxLayout | None = None
        if title or subtitle:
            self.set_header(title, subtitle)

    def set_header(self, title: str, subtitle: str = "") -> None:
        if self.header is None:
            self.header = QHBoxLayout()
            self.header.setSpacing(10)
            self._outer.addLayout(self.header)

        self.header_label = QLabel(title)
        self.header_label.setFont(brand.font(15, QFont.Weight.DemiBold))
        self.header_label.setStyleSheet(f"color:{brand.TEXT}; background: transparent; border: none;")
        self.header.addWidget(self.header_label)

        self.header_actions = QHBoxLayout()
        self.header_actions.setSpacing(8)
        self.header.addLayout(self.header_actions)
        self.header.addStretch(1)

        if subtitle:
            self.header_subtitle = QLabel(subtitle)
            self.header_subtitle.setFont(brand.font(11))
            self.header_subtitle.setStyleSheet(f"color:{brand.MUTED}; background: transparent; border: none;")
            self._outer.insertWidget(1, self.header_subtitle)

    def add(self, widget: QWidget) -> QWidget:
        if self.body is None:
            self.body = QVBoxLayout()
            self.body.setSpacing(12)
            self.body.setContentsMargins(0, 0, 0, 0)
            self._outer.addLayout(self.body)
        self.body.addWidget(widget)
        return widget

    def add_layout(self, layout) -> None:
        if self.body is None:
            self.body = QVBoxLayout()
            self.body.setSpacing(12)
            self.body.setContentsMargins(0, 0, 0, 0)
            self._outer.addLayout(self.body)
        self.body.addLayout(layout)

    def add_stretch(self, factor: int = 1) -> None:
        if self.body is None:
            self.body = QVBoxLayout()
            self.body.setContentsMargins(0, 0, 0, 0)
            self._outer.addLayout(self.body)
        self.body.addStretch(factor)


class StatTile(QFrame):
    """Compact KPI tile with an accent bar, a value and a caption."""

    def __init__(
        self,
        label: str,
        value: str,
        hint: str = "",
        accent: str = brand.PRIMARY,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("StatTile")
        self.setStyleSheet(
            f"""
            QFrame#StatTile {{
                background: {brand.CARD};
                border: 1px solid {brand.BORDER};
                border-radius: 12px;
            }}
            QFrame#StatTile QLabel {{
                background: transparent;
                border: none;
            }}
            """
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        bar = QFrame()
        bar.setFixedWidth(4)
        bar.setStyleSheet(f"background:{accent}; border-radius:2px;")
        layout.addWidget(bar)

        col = QVBoxLayout()
        col.setSpacing(1)
        self.value_label = QLabel(value)
        self.value_label.setFont(brand.font(21, QFont.Weight.Bold))
        self.value_label.setStyleSheet(f"color:{brand.TEXT}; background: transparent; border: none;")
        col.addWidget(self.value_label)

        self.label_widget = QLabel(label)
        self.label_widget.setFont(brand.font(12, QFont.Weight.DemiBold))
        self.label_widget.setStyleSheet(f"color:{brand.TEXT_SOFT}; background: transparent; border: none;")
        col.addWidget(self.label_widget)

        if hint:
            self.hint_widget = QLabel(hint)
            self.hint_widget.setFont(brand.font(10))
            self.hint_widget.setStyleSheet(f"color:{brand.MUTED}; background: transparent; border: none;")
            col.addWidget(self.hint_widget)

        layout.addLayout(col)
        layout.addStretch(1)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class TipBox(QFrame):
    """Soft callout box, as used for hints under the run button."""

    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("TipBox")
        self.setStyleSheet(
            f"""
            QFrame#TipBox {{
                background: {brand.PRIMARY_SOFT};
                border: 1px solid {brand.PRIMARY_BORDER};
                border-radius: 10px;
            }}
            QFrame#TipBox QLabel {{
                background: transparent;
                border: none;
            }}
            """
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        self.bulb = IconWidgetHost("bulb", brand.PRIMARY)
        self.bulb.setFixedSize(20, 20)
        layout.addWidget(self.bulb)

        self.label = QLabel(text)
        self.label.setFont(brand.font(12))
        self.label.setWordWrap(True)
        self.label.setStyleSheet(f"color:{brand.TEXT_SOFT}; background: transparent; border: none;")
        layout.addWidget(self.label, 1)


class IconWidgetHost(QWidget):
    """A tiny widget that paints one brand icon."""

    def __init__(self, name: str, color: str = brand.PRIMARY, parent: QWidget | None = None):
        super().__init__(parent)
        self.icon_name = name
        self.icon_color = color

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        brand.paint_icon(painter, self.icon_name, rect, self.icon_color, 1.7)
        painter.end()


class ElidedLabel(QLabel):
    """A label that shortens its text with an ellipsis instead of clipping."""

    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self._full_text = text
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def setText(self, text: str) -> None:  # noqa: N802
        self._full_text = text
        self.setToolTip(text)
        self.update()

    def full_text(self) -> str:
        return self._full_text

    def paintEvent(self, event):  # noqa: N802
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(
            self._full_text, Qt.TextElideMode.ElideRight, self.width()
        )
        painter = QPainter(self)
        painter.setFont(self.font())
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.drawText(
            self.rect(), int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), elided
        )
        painter.end()


class LogoWidget(QWidget):
    """The brand mark; optionally with the wordmark next to it."""

    def __init__(self, size: int = 44, parent: QWidget | None = None):
        super().__init__(parent)
        self.mark_size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        brand.paint_logo(painter, QRectF(self.rect()))
        painter.end()


# --------------------------------------------------------------------------
# Navigation
# --------------------------------------------------------------------------
class NavButton(QPushButton):
    """Sidebar navigation entry with a vector icon and active state."""

    def __init__(self, text: str, icon: str, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.icon_name = icon
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(42)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setIconSize(QSize(19, 19))
        self._icon_color = brand.SIDEBAR_TEXT
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                color: {brand.SIDEBAR_TEXT};
                border: none;
                border-radius: 9px;
                text-align: right;
                padding: 8px 14px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.06);
                color: #E2E8F0;
            }}
            QPushButton:checked {{
                background: {brand.PRIMARY};
                color: {brand.SIDEBAR_TEXT_ACTIVE};
                font-weight: 600;
            }}
            """
        )

    def set_toggled(self, active: bool) -> None:
        self._icon_color = brand.SIDEBAR_TEXT_ACTIVE if active else brand.SIDEBAR_TEXT
        self.update()

    def paintEvent(self, event):  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        side = 18
        rect = QRectF(self.width() - side - 16, (self.height() - side) / 2, side, side)
        brand.paint_icon(painter, self.icon_name, rect, self._icon_color, 1.7)
        painter.end()


# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------
_SORT_UP, _SORT_DOWN = _sort_arrow_assets()

TABLE_QSS = f"""
QTableView {{
    background: {brand.CARD};
    alternate-background-color: #F8FAFC;
    border: 1px solid {brand.BORDER};
    border-radius: 10px;
    gridline-color: #EDF2F7;
    selection-background-color: {brand.PRIMARY_SOFT};
    selection-color: {brand.TEXT};
    font-size: 13px;
}}
QTableView::item {{
    padding: 7px 10px;
    border: none;
}}
QTableView::item:selected {{
    background: {brand.PRIMARY_SOFT};
    color: {brand.TEXT};
}}
QHeaderView {{ background: {brand.NAVY}; }}
QHeaderView::section {{
    background: {brand.NAVY};
    color: #FFFFFF;
    padding: 9px 26px 9px 12px;
    border: none;
    font-weight: 600;
    font-size: 12px;
}}
QTableCornerButton::section {{ background: {brand.NAVY}; border: none; }}
QHeaderView::up-arrow {{ image: url({_SORT_UP}); width: 11px; height: 11px; }}
QHeaderView::down-arrow {{ image: url({_SORT_DOWN}); width: 11px; height: 11px; }}
"""


def make_table(headers: Sequence[str], rows: Iterable[Sequence[str]], max_rows: int = 0) -> QTableView:
    """Build a styled, sortable table."""
    from PyQt6.QtGui import QStandardItem, QStandardItemModel

    table = QTableView()
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
    table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
    table.setSortingEnabled(True)
    table.setShowGrid(False)
    table.setWordWrap(False)
    table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    table.setStyleSheet(TABLE_QSS)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(36)
    table.horizontalHeader().setHighlightSections(False)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setDefaultAlignment(
        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
    )
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.horizontalHeader().setMinimumSectionSize(70)
    table.setFrameShape(QFrame.Shape.NoFrame)

    model = QStandardItemModel()
    model.setHorizontalHeaderLabels(list(headers))
    for row in rows:
        if max_rows and model.rowCount() >= max_rows:
            break
        items = []
        for value in row:
            item = QStandardItem("" if value is None else str(value))
            item.setEditable(False)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            items.append(item)
        model.appendRow(items)
    table.setModel(model)
    return table


def resize_columns(table: QTableView, ratios: Sequence[float] | None = None) -> None:
    """Stretch columns proportionally to the table width."""
    from PyQt6.QtWidgets import QHeaderView

    header = table.horizontalHeader()
    if ratios:
        total = sum(ratios)
        for i, ratio in enumerate(ratios):
            if i < header.count():
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        table._ratios = list(ratios)  # type: ignore[attr-defined]
    else:
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)


def resize_last_stretch(table: QTableView) -> None:
    from PyQt6.QtWidgets import QHeaderView

    header = table.horizontalHeader()
    for i in range(header.count()):
        header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
    if header.count():
        header.setSectionResizeMode(header.count() - 1, QHeaderView.ResizeMode.Stretch)
