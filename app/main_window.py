"""Main window: branded sidebar navigation, header band and page stack."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from . import brand
from .components import ElidedLabel, LogoWidget, NavButton
from .controller import Controller
from .pages import (
    AboutPage,
    AnalysisPage,
    DataPage,
    ExportPage,
    HomePage,
    ResultsPage,
    GrowthArt,
)

NAV_ITEMS = [
    ("home", "الرئيسية", "home"),
    ("data", "البيانات", "data"),
    ("analysis", "التحليل", "analysis"),
    ("results", "النتائج", "results"),
    ("export", "التصدير", "export"),
    ("about", "عن الأداة", "about"),
]


class HeaderBand(QFrame):
    """The light banner at the top of the content area."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(112)
        self.setStyleSheet("border: none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(26, 14, 26, 14)
        layout.setSpacing(16)

        right = QHBoxLayout()
        right.setSpacing(14)
        self.logo = LogoWidget(52)
        right.addWidget(self.logo)

        texts = QVBoxLayout()
        texts.setSpacing(2)
        title = QLabel("أداة تحليل سلة المشتريات")
        title.setFont(brand.font(23, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{brand.TEXT}; background: transparent; border: none;")
        texts.addWidget(title)

        subtitle = ElidedLabel("اكتشف المنتجات التي تُشترى معًا باستخدام خوارزمية Apriori")
        subtitle.setFont(brand.font(12))
        subtitle.setStyleSheet(f"color:{brand.MUTED}; background: transparent; border: none;")
        texts.addWidget(subtitle)
        right.addLayout(texts)

        layout.addLayout(right)
        layout.addStretch(1)

        self.art = GrowthArt()
        layout.addWidget(self.art)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor("#FFFFFF"))
        gradient.setColorAt(1.0, QColor("#E8F0FE"))
        painter.fillRect(self.rect(), gradient)
        painter.setPen(QPen(QColor(brand.BORDER), 1))
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        painter.end()


class Sidebar(QFrame):
    """Dark navigation rail."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedWidth(214)
        self.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 {brand.NAVY}, stop:1 {brand.NAVY_DEEP});
                border: none;
            }}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 18, 14, 16)
        layout.setSpacing(6)

        # Brand block
        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        mark = LogoWidget(40)
        brand_row.addWidget(mark)
        names = QVBoxLayout()
        names.setSpacing(0)
        name = QLabel("سَلّة")
        name.setFont(brand.font(17, QFont.Weight.Bold))
        name.setStyleSheet("color:#FFFFFF;")
        names.addWidget(name)
        tagline = QLabel("Market Basket Analysis")
        tagline.setFont(brand.font(9))
        tagline.setStyleSheet(f"color:{brand.SIDEBAR_TEXT}; background: transparent; border: none;")
        names.addWidget(tagline)
        brand_row.addLayout(names)
        brand_row.addStretch(1)
        layout.addLayout(brand_row)
        layout.addSpacing(18)

        self.buttons: dict[str, NavButton] = {}
        for key, label, icon in NAV_ITEMS:
            button = NavButton(label, icon)
            self.buttons[key] = button
            layout.addWidget(button)

        layout.addStretch(1)

        footer = QLabel("الإصدار 1.0.0")
        footer.setFont(brand.font(10))
        footer.setStyleSheet(f"color:{brand.SIDEBAR_TEXT}; background: transparent; border: none;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

    def paintEvent(self, event):  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(brand.NAVY_LINE), 1))
        painter.drawLine(0, 0, 0, self.height())
        painter.end()


class MainWindow(QMainWindow):
    """The application shell."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("سَلّة — أداة تحليل سلة المشتريات")
        self.setMinimumSize(1240, 780)
        self.resize(1440, 900)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.controller = Controller(self)

        central = QWidget()
        central.setStyleSheet(f"background:{brand.BG};")
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        self.sidebar = Sidebar()
        central_layout.addWidget(self.sidebar)

        content = QWidget()
        content.setStyleSheet(f"background:{brand.BG};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.header = HeaderBand()
        content_layout.addWidget(self.header)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background:{brand.BG};")
        content_layout.addWidget(self.stack, 1)

        central_layout.addWidget(content, 1)
        self.setCentralWidget(central)

        self.pages = {
            "home": HomePage(self.controller),
            "data": DataPage(self.controller),
            "analysis": AnalysisPage(self.controller),
            "results": ResultsPage(self.controller),
            "export": ExportPage(self.controller),
            "about": AboutPage(self.controller),
        }
        for key, page in self.pages.items():
            self.stack.addWidget(page)

        for key, button in self.sidebar.buttons.items():
            button.clicked.connect(lambda _=False, k=key: self.navigate(k))

        self.pages["home"].navigate.connect(self.navigate)
        self.pages["data"].navigate.connect(self.navigate)

        self.controller.data_changed.connect(self._on_data_changed)
        self.controller.results_changed.connect(self._on_results_changed)
        self.controller.status_changed.connect(self._on_status)

        status = QStatusBar()
        status.setStyleSheet(
            f"""
            QStatusBar {{
                background: {brand.NAVY};
                color: #CBD5E1;
                font-size: 12px;
            }}
            """
        )
        self.setStatusBar(status)
        self.status_label = QLabel("جاهز")
        self.status_label.setStyleSheet("color:#CBD5E1;")
        status.addWidget(self.status_label, 1)

        self.navigate("home")

    # -- navigation ---------------------------------------------------------
    def navigate(self, key: str) -> None:
        if key not in self.pages:
            return
        self.stack.setCurrentWidget(self.pages[key])
        for nav_key, button in self.sidebar.buttons.items():
            button.setChecked(nav_key == key)
            button.set_toggled(nav_key == key)

    # -- reactions ----------------------------------------------------------
    def _on_data_changed(self) -> None:
        self.pages["home"].refresh()
        self.pages["data"].refresh()
        self.pages["analysis"].refresh()
        self.pages["export"].refresh()

    def _on_results_changed(self) -> None:
        self.pages["home"].refresh()
        self.pages["analysis"].refresh()
        self.pages["results"].refresh()
        self.pages["export"].refresh()

    def _on_status(self, message: str) -> None:
        self.status_label.setText(message)
