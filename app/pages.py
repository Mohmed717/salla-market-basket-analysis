"""Application pages: Home, Data, Analysis, Results, Export and About."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Sequence

from PyQt6.QtCore import QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from . import brand, charts
from .components import (
    Card,
    GhostButton,
    IconWidgetHost,
    LogoWidget,
    PrimaryButton,
    StatTile,
    TipBox,
    make_table,
)
from .controller import Controller


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------
class GrowthArt(QWidget):
    """Decorative rising-chart illustration used in the header."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(124, 84)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()

        gradient = QLinearGradient(0, 0, w, h)
        gradient.setColorAt(0.0, QColor(brand.PRIMARY_SOFT))
        gradient.setColorAt(1.0, QColor("#E0EDFF"))
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(0, 0, w, h), 18, 18)

        pen = QPen(QColor(brand.PRIMARY))
        pen.setWidthF(3.4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        points = [
            (22, h - 26),
            (44, h - 42),
            (66, h - 36),
            (88, h - 58),
            (110, h - 74),
        ]
        for i in range(len(points) - 1):
            painter.drawLine(*points[i], *points[i + 1])

        painter.setBrush(QColor(brand.PRIMARY))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(points[-1][0] - 5, points[-1][1] - 5, 10, 10))

        pen.setColor(QColor("#FFFFFF"))
        pen.setWidthF(2.6)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(points[-1][0] + 2, points[-1][1] - 12, points[-1][0] + 12, points[-1][1] - 22)
        painter.drawLine(points[-1][0] + 12, points[-1][1] - 22, points[-1][0] + 5, points[-1][1] - 23)
        painter.drawLine(points[-1][0] + 12, points[-1][1] - 22, points[-1][0] + 13, points[-1][1] - 15)

        painter.setPen(QPen(QColor("#BFDBFE"), 2))
        for i, x in enumerate(range(26, w - 16, 24)):
            painter.drawLine(x, h - 16, x, h - 16 - (8 + i * 5))
        painter.end()


class SectionTitle(QWidget):
    """A page-level heading with an accent rule."""

    def __init__(self, title: str, subtitle: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_label = QLabel(title)
        title_label.setFont(brand.font(19, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color:{brand.TEXT}; background: transparent; border: none;")
        text_col.addWidget(title_label)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setFont(brand.font(12))
            sub.setStyleSheet(f"color:{brand.MUTED}; background: transparent; border: none;")
            text_col.addWidget(sub)
        layout.addLayout(text_col)
        layout.addStretch(1)


def scrollable(widget: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setStyleSheet(
        f"""
        QScrollArea {{ background: {brand.BG}; border: none; }}
        QScrollArea > QWidget > QWidget {{ background: {brand.BG}; }}
        """
    )
    area.setWidget(widget)
    return area


def find_sample_dataset(name: str = "sample_transactions.csv") -> Path | None:
    """Locate the bundled sample dataset, in source and frozen builds alike."""
    import sys

    candidates = [
        Path(__file__).resolve().parents[1] / "data" / name,
        Path(__file__).resolve().parent / "data" / name,
        Path.cwd() / "data" / name,
    ]
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        candidates.append(Path(bundle) / "data" / name)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def page_scaffold() -> tuple[QWidget, QVBoxLayout]:
    """A scrollable page shell returning the inner widget and its layout."""
    outer = QWidget()
    outer.setStyleSheet(f"background:{brand.BG};")
    layout = QVBoxLayout(outer)
    layout.setContentsMargins(26, 20, 26, 26)
    layout.setSpacing(18)
    return outer, layout


def styled_spin(inner: str = "") -> str:
    return f"""
    QSpinBox, QDoubleSpinBox, QComboBox {{
        background: {brand.CARD};
        border: 1px solid {brand.BORDER_STRONG};
        border-radius: 8px;
        padding: 7px 10px;
        min-height: 22px;
        color: {brand.TEXT};
        font-size: 13px;
    }}
    QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border-color: {brand.PRIMARY};
    }}
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        width: 16px; border: none; background: transparent;
    }}
    {inner}
    """


# --------------------------------------------------------------------------
# Home
# --------------------------------------------------------------------------
class HomePage(QWidget):
    navigate = pyqtSignal(str)

    def __init__(self, controller: Controller, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller
        outer, layout = page_scaffold()
        self.setLayout(layout)
        layout.addWidget(self._hero())
        layout.addWidget(self._kpis())
        layout.addWidget(self._steps())
        layout.addStretch(1)
        self.refresh()

    def _hero(self) -> QWidget:
        card = Card()
        row = QHBoxLayout()
        row.setSpacing(26)

        left = QVBoxLayout()
        left.setSpacing(8)
        brand_row = QHBoxLayout()
        brand_row.setSpacing(12)
        mark = LogoWidget(52)
        brand_row.addWidget(mark)
        names = QVBoxLayout()
        names.setSpacing(0)
        title = QLabel("سَلّة")
        title.setFont(brand.font(30, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{brand.TEXT}; background: transparent; border: none;")
        names.addWidget(title)
        sub = QLabel("منصّة تحليل سلة المشتريات")
        sub.setFont(brand.font(13))
        sub.setStyleSheet(f"color:{brand.MUTED}; background: transparent; border: none;")
        names.addWidget(sub)
        brand_row.addLayout(names)
        brand_row.addStretch(1)
        left.addLayout(brand_row)

        desc = QLabel(
            "اكتشف المنتجات التي تُشترى معًا داخل متجرك، باستخدام خوارزمية Apriori "
            "المكتوبة من الصفر. حوّل سجلّ المعاملات إلى قرارات عرض وتسويق فورية."
        )
        desc.setFont(brand.font(13))
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{brand.TEXT_SOFT}; background: transparent; border: none;")
        desc.setMaximumWidth(560)
        left.addWidget(desc)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        load_btn = PrimaryButton("تحميل ملف البيانات", "folder")
        load_btn.clicked.connect(lambda: self.navigate.emit("data"))
        buttons.addWidget(load_btn)
        analysis_btn = GhostButton("الانتقال للتحليل", "analysis")
        analysis_btn.clicked.connect(lambda: self.navigate.emit("analysis"))
        buttons.addWidget(analysis_btn)
        buttons.addStretch(1)
        left.addLayout(buttons)
        left.addStretch(1)
        row.addLayout(left, 1)

        art = GrowthArt()
        row.addWidget(art, 0, Qt.AlignmentFlag.AlignVCenter)
        card.add_layout(row)
        return card

    def _kpis(self) -> QWidget:
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)
        self.kpi_transactions = StatTile("المعاملات", "—", "لم يتم تحميل ملف", brand.PRIMARY)
        self.kpi_items = StatTile("المنتجات الفريدة", "—", "منتج مختلف", brand.TEAL)
        self.kpi_basket = StatTile("متوسط حجم السلة", "—", "منتج لكل معاملة", brand.GREEN)
        self.kpi_rules = StatTile("قواعد الارتباط", "—", "قاعدة قابلة للتنفيذ", brand.AMBER)
        for tile in (self.kpi_transactions, self.kpi_items, self.kpi_basket, self.kpi_rules):
            row.addWidget(tile)
        return holder

    def _steps(self) -> QWidget:
        card = Card("كيف تعمل الأداة؟", "أربع خطوات من الملف إلى قرار التسويق")
        grid = QGridLayout()
        grid.setSpacing(14)
        steps = [
            ("1", "تحميل البيانات", "ارفع ملف CSV بالمعاملات. يدعم الأداة ثلاثة تنسيقات: سلة في صف واحد، سجل طويل، أو جدول عريض بأعمدة 0/1.", brand.PRIMARY),
            ("2", "ضبط المعاملات", "حدّد الحد الأدنى للدعم والثقة، وطول أكبر مجموعة عناصر تريد استخراجها.", brand.TEAL),
            ("3", "استخراج المتجهات المتكررة", "تعمل خوارزمية Apriori على توليد المرشحين وقصّهم، ثم حساب الدعم لكل مجموعة.", brand.GREEN),
            ("4", "اكتشاف القواعد", "استخراج قواعد الارتباط مع الثقة والرفع، وتصدير النتائج بصيغة CSV جاهزة للعرض.", brand.AMBER),
        ]
        for i, (num, head, body, color) in enumerate(steps):
            tile = QFrame()
            tile.setObjectName("Tile")
            tile.setStyleSheet(
                f"""
                QFrame#Tile {{
                    background: #F8FAFC;
                    border: 1px solid {brand.BORDER};
                    border-radius: 12px;
                }}
                QFrame#Tile QLabel {{
                    background: transparent;
                    border: none;
                }}
                """
            )
            col = QVBoxLayout(tile)
            col.setContentsMargins(16, 14, 16, 14)
            col.setSpacing(6)

            top = QHBoxLayout()
            badge = QLabel(num)
            badge.setFixedSize(28, 28)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFont(brand.font(14, QFont.Weight.Bold))
            badge.setStyleSheet(
                f"background:{color}; color:#FFFFFF; border-radius:9px;"
            )
            top.addWidget(badge)
            head_label = QLabel(head)
            head_label.setFont(brand.font(14, QFont.Weight.DemiBold))
            head_label.setStyleSheet(f"color:{brand.TEXT}; background: transparent; border: none;")
            top.addWidget(head_label)
            top.addStretch(1)
            col.addLayout(top)

            body_label = QLabel(body)
            body_label.setFont(brand.font(12))
            body_label.setWordWrap(True)
            body_label.setStyleSheet(f"color:{brand.MUTED}; background: transparent; border: none;")
            col.addWidget(body_label)

            grid.addWidget(tile, i // 2, i % 2)
        card.add_layout(grid)
        return card

    def refresh(self) -> None:
        st = self.controller.state
        if st.has_data:
            dataset = st.dataset
            self.kpi_transactions.set_value(f"{dataset.n_transactions:,}")
            self.kpi_transactions.hint_widget.setText("معاملة محمّلة")
            self.kpi_items.set_value(f"{dataset.n_items:,}")
            self.kpi_items.hint_widget.setText("منتج فريد")
            self.kpi_basket.set_value(f"{dataset.avg_basket_size:.2f}")
            self.kpi_basket.hint_widget.setText("منتج لكل معاملة")
            if st.has_results:
                self.kpi_rules.set_value(f"{len(st.rules.rules):,}")
                self.kpi_rules.hint_widget.setText("قاعدة قابلة للتنفيذ")
            else:
                self.kpi_rules.set_value("—")
                self.kpi_rules.hint_widget.setText("لم يُشغَّل التحليل بعد")
        else:
            for tile, hint in (
                (self.kpi_transactions, "لم يتم تحميل ملف"),
                (self.kpi_items, "منتج مختلف"),
                (self.kpi_basket, "منتج لكل معاملة"),
                (self.kpi_rules, "قاعدة قابلة للتنفيذ"),
            ):
                tile.set_value("—")
                tile.hint_widget.setText(hint)


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------
class DataPage(QWidget):
    navigate = pyqtSignal(str)

    def __init__(self, controller: Controller, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller
        outer, layout = page_scaffold()
        self.setLayout(layout)
        layout.addWidget(SectionTitle("البيانات", "ارفع ملف المعاملات وتعرّف على بنيته"))
        layout.addWidget(self._source_card())
        layout.addWidget(self._stats_card())
        layout.addWidget(self._preview_card(), 1)
        self.refresh()

    def _source_card(self) -> QWidget:
        card = Card("ملف البيانات")
        row = QHBoxLayout()
        row.setSpacing(12)

        self.load_button = PrimaryButton("تحميل ملف CSV", "folder")
        self.load_button.clicked.connect(self._choose_file)
        row.addWidget(self.load_button)

        self.sample_button = GhostButton("استخدام بيانات تجريبية", "play")
        self.sample_button.clicked.connect(self._load_sample)
        row.addWidget(self.sample_button)

        row.addStretch(1)

        self.status_icon = IconWidgetHost("check", brand.GREEN)
        self.status_icon.setFixedSize(18, 18)
        row.addWidget(self.status_icon)

        self.file_label = QLabel("لم يتم تحميل أي ملف بعد")
        self.file_label.setFont(brand.font(13, QFont.Weight.DemiBold))
        self.file_label.setStyleSheet(f"color:{brand.TEXT_SOFT}; background: transparent; border: none;")
        row.addWidget(self.file_label)
        card.add_layout(row)

        self.format_label = QLabel("")
        self.format_label.setFont(brand.font(12))
        self.format_label.setStyleSheet(f"color:{brand.MUTED}; background: transparent; border: none;")
        card.add(self.format_label)
        return card

    def _stats_card(self) -> QWidget:
        card = Card("إحصائيات الملف")
        holder = QWidget()
        row = QHBoxLayout(holder)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)
        self.stat_rows = StatTile("عدد الصفوف", "—", "صف في الملف", brand.PRIMARY)
        self.stat_tx = StatTile("المعاملات", "—", "سلة مشتريات", brand.TEAL)
        self.stat_items = StatTile("المنتجات", "—", "اسم فريد", brand.GREEN)
        self.stat_avg = StatTile("متوسط السلة", "—", "منتج/معاملة", brand.AMBER)
        self.stat_max = StatTile("أكبر سلة", "—", "منتج في معاملة", brand.PURPLE)
        for tile in (self.stat_rows, self.stat_tx, self.stat_items, self.stat_avg, self.stat_max):
            row.addWidget(tile)
        card.add(holder)
        return card

    def _preview_card(self) -> QWidget:
        card = Card("معاينة المعاملات", "أول 30 معاملة بعد التطبيع")
        self.preview = make_table(["رقم المعاملة", "المنتجات", "العدد"], [])
        self.preview.setMinimumHeight(220)
        card.add(self.preview)
        return card

    def _choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف المعاملات", "", "ملفات CSV (*.csv *.tsv *.txt);;كل الملفات (*)"
        )
        if path:
            self.controller.load_file(path)
            self.refresh()

    def _load_sample(self) -> None:
        sample = find_sample_dataset()
        if sample is None:
            QMessageBox.warning(self, "بيانات تجريبية", "ملف البيانات التجريبية غير موجود.")
            return
        self.controller.load_file(str(sample))
        self.refresh()

    def refresh(self) -> None:
        st = self.controller.state
        if not st.has_data:
            self.file_label.setText("لم يتم تحميل أي ملف بعد")
            self.status_icon.icon_color = brand.MUTED_LIGHT
            self.status_icon.update()
            self.format_label.setText("")
            for tile in (self.stat_rows, self.stat_tx, self.stat_items, self.stat_avg, self.stat_max):
                tile.set_value("—")
            return

        dataset = st.dataset
        self.file_label.setText(dataset.source_name or "ملف محمّل")
        self.status_icon.icon_color = brand.GREEN
        self.status_icon.update()

        fmt_names = {
            "basket": "سلة في صف واحد (Basket)",
            "long": "سجل طويل (Long / Transaction-Item)",
            "wide": "جدول عريض (Wide / 0-1 Matrix)",
        }
        details = [fmt_names.get(dataset.format, dataset.format)]
        if dataset.item_column:
            details.append(f"عمود المنتجات: {dataset.item_column}")
        if dataset.id_column:
            details.append(f"عمود المعرّف: {dataset.id_column}")
        delimiter_names = {",": "فاصلة", ";": "فاصلة منقوطة", "|": "شرطة رأسية", "\t": "مسافة جدولة"}
        details.append(f"الفاصل: {delimiter_names.get(dataset.delimiter, dataset.delimiter)}")
        self.format_label.setText("  •  ".join(details))

        self.stat_rows.set_value(f"{dataset.n_rows:,}")
        self.stat_tx.set_value(f"{dataset.n_transactions:,}")
        self.stat_items.set_value(f"{dataset.n_items:,}")
        self.stat_avg.set_value(f"{dataset.avg_basket_size:.2f}")
        self.stat_max.set_value(f"{max(dataset.basket_sizes) if dataset.basket_sizes else 0}")

        rows = []
        for tid, basket in list(zip(dataset.transaction_ids, dataset.transactions))[:30]:
            rows.append([tid, " | ".join(sorted(basket)), len(basket)])
        model = self.preview.model()
        model.setRowCount(0)
        from PyQt6.QtGui import QStandardItem

        for row in rows:
            items = []
            for value in row:
                item = QStandardItem(str(value))
                item.setEditable(False)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                items.append(item)
            model.appendRow(items)


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------
class AnalysisPage(QWidget):
    navigate = pyqtSignal(str)

    def __init__(self, controller: Controller, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller
        outer, layout = page_scaffold()
        self.setLayout(layout)
        layout.addWidget(SectionTitle("التحليل", "اضبط معاملات خوارزمية Apriori ثم شغّلها"))

        columns = QHBoxLayout()
        columns.setSpacing(18)

        left = QVBoxLayout()
        left.setSpacing(18)
        left.addWidget(self._params_card())
        left.addWidget(self._run_card())
        columns.addLayout(left, 0)

        right = QVBoxLayout()
        right.setSpacing(18)
        right.addWidget(self._preview_rules_card())
        columns.addLayout(right, 1)

        layout.addLayout(columns)
        layout.addStretch(1)
        self.refresh()

    def _params_card(self) -> QWidget:
        card = Card("معاملات الخوارزمية")

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.support_spin = QSpinBox()
        self.support_spin.setRange(1, 100)
        self.support_spin.setValue(int(self.controller.state.min_support * 100))
        self.support_spin.setSuffix(" %")
        self.support_spin.setFixedWidth(150)
        self.support_spin.valueChanged.connect(self._on_params_changed)

        self.confidence_spin = QSpinBox()
        self.confidence_spin.setRange(1, 100)
        self.confidence_spin.setValue(int(self.controller.state.min_confidence * 100))
        self.confidence_spin.setSuffix(" %")
        self.confidence_spin.setFixedWidth(150)
        self.confidence_spin.valueChanged.connect(self._on_params_changed)

        self.lift_spin = QDoubleSpinBox()
        self.lift_spin.setRange(0.0, 10.0)
        self.lift_spin.setSingleStep(0.1)
        self.lift_spin.setDecimals(2)
        self.lift_spin.setValue(self.controller.state.min_lift)
        self.lift_spin.setFixedWidth(150)
        self.lift_spin.valueChanged.connect(self._on_params_changed)

        self.len_spin = QSpinBox()
        self.len_spin.setRange(1, 5)
        self.len_spin.setValue(self.controller.state.max_len)
        self.len_spin.setFixedWidth(150)
        self.len_spin.valueChanged.connect(self._on_params_changed)

        form.addRow(self._field_label("الحد الأدنى للدعم (Minimum Support)"), self.support_spin)
        form.addRow(self._field_label("الحد الأدنى للثقة (Minimum Confidence)"), self.confidence_spin)
        form.addRow(self._field_label("الحد الأدنى للرفع (Minimum Lift)"), self.lift_spin)
        form.addRow(self._field_label("أقصى طول للمجموعة (Max Itemset Length)"), self.len_spin)

        holder = QWidget()
        holder.setStyleSheet(styled_spin())
        holder.setLayout(form)
        card.add(holder)

        tip = TipBox(
            "استخدم دعمًا أقل لاكتشاف أنماط أوسع وأكثر، وارفعه عند الحاجة إلى تركيز النتائج "
            "على الأنماط الأكثر تكرارًا."
        )
        card.add(tip)
        return card

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setFont(brand.font(12, QFont.Weight.DemiBold))
        label.setStyleSheet(f"color:{brand.TEXT_SOFT}; background: transparent; border: none;")
        return label

    def _run_card(self) -> QWidget:
        card = Card("التنفيذ")
        self.run_button = PrimaryButton("تشغيل خوارزمية Apriori", "play")
        self.run_button.clicked.connect(self._run)
        card.add(self.run_button)

        self.status_label = QLabel("جاهز للتشغيل")
        self.status_label.setFont(brand.font(12))
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(f"color:{brand.MUTED}; background: transparent; border: none;")
        card.add(self.status_label)
        return card

    def _preview_rules_card(self) -> QWidget:
        card = Card("أفضل 10 قواعد ارتباط", "Antecedent ← Consequent — تُحدَّث فور انتهاء التشغيل")
        self.rules_table = make_table(
            ["المُقدِّم", "المُتْبَع", "الدعم", "الثقة", "الرفع"], []
        )
        self.rules_table.setMinimumHeight(260)
        card.add(self.rules_table)
        self.summary_label = QLabel("")
        self.summary_label.setFont(brand.font(12))
        self.summary_label.setStyleSheet(f"color:{brand.MUTED}; background: transparent; border: none;")
        card.add(self.summary_label)
        return card

    def _on_params_changed(self) -> None:
        st = self.controller.state
        st.min_support = self.support_spin.value() / 100
        st.min_confidence = self.confidence_spin.value() / 100
        st.min_lift = self.lift_spin.value()
        st.max_len = self.len_spin.value()
        st.reset_results()
        self.controller.results_changed.emit()

    def _run(self) -> None:
        self.controller.run_analysis()
        self.status_label.setText("جارٍ التنفيذ…")
        self.run_button.setEnabled(False)

    def on_finished(self) -> None:
        self.run_button.setEnabled(True)
        self.refresh()

    def refresh(self) -> None:
        st = self.controller.state
        if not st.has_data:
            self.run_button.setEnabled(False)
            self.status_label.setText("الرجاء تحميل ملف بيانات في صفحة «البيانات» أولاً.")
            return
        self.run_button.setEnabled(True)

        if st.has_results:
            self.status_label.setText(
                f"اكتمل التحليل في {st.runtime:.2f} ثانية — "
                f"{len(st.result.itemsets):,} مجموعة متكررة، "
                f"{len(st.rules.rules):,} قاعدة ارتباط."
            )
            from PyQt6.QtGui import QStandardItem

            model = self.rules_table.model()
            model.setRowCount(0)
            for rule in st.rules.rules[:10]:
                values = [
                    rule.antecedent_label,
                    rule.consequent_label,
                    f"{rule.support:.3f}",
                    f"{rule.confidence:.3f}",
                    f"{rule.lift:.2f}",
                ]
                items = []
                for value in values:
                    item = QStandardItem(value)
                    item.setEditable(False)
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    items.append(item)
                model.appendRow(items)

            best = st.rules.best_rule
            if best:
                self.summary_label.setText(
                    f"أقوى قاعدة: {best.antecedent_label} ← {best.consequent_label} "
                    f"(ثقة {best.confidence:.0%}، رفع {best.lift:.2f})"
                )
        else:
            self.status_label.setText("جاهز للتشغيل — اضغط «تشغيل خوارزمية Apriori».")
            self.summary_label.setText("")


# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------
class ResultsPage(QWidget):
    def __init__(self, controller: Controller, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller
        outer, layout = page_scaffold()
        self.setLayout(layout)
        layout.addWidget(SectionTitle("النتائج", "المتجهات المتكررة، قواعد الارتباط، والتحليلات البيانية"))
        layout.addWidget(self._tabs())
        self.refresh()

    def _tabs(self) -> QWidget:
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: 1px solid {brand.BORDER};
                border-radius: 12px;
                background: {brand.BG};
                top: -1px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {brand.MUTED};
                padding: 9px 20px;
                margin-left: 4px;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {brand.CARD};
                color: {brand.PRIMARY};
                border: 1px solid {brand.BORDER};
                border-bottom: 2px solid {brand.PRIMARY};
            }}
            QTabBar::tab:hover {{ color: {brand.TEXT}; }}
            """
        )

        self.tabs.addTab(self._itemsets_tab(), "المتجهات المتكررة")
        self.tabs.addTab(self._rules_tab(), "قواعد الارتباط")
        self.tabs.addTab(self._charts_tab(), "الرسوم البيانية")
        self.tabs.addTab(self._summary_tab(), "الملخص والتوصيات")
        return self.tabs

    def _itemsets_tab(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background:{brand.BG};")
        split = QSplitter(Qt.Orientation.Vertical)

        self.itemsets_table = make_table(
            ["المجموعة المتكررة", "الحجم", "الدعم", "عدد المعاملات"], []
        )
        table_card = Card("جدول المتجهات المتكررة")
        table_card.add(self.itemsets_table)

        self.itemsets_chart_canvas = charts.canvas_for(charts.Figure(figsize=(6, 3)))
        self.itemsets_chart_card = Card("أعلى المتجهات المتكررة")
        self.itemsets_chart_card.add(self.itemsets_chart_canvas)

        split.addWidget(table_card)
        split.addWidget(self.itemsets_chart_card)
        split.setSizes([420, 340])

        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.addWidget(split)
        return page

    def _rules_tab(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background:{brand.BG};")
        split = QSplitter(Qt.Orientation.Vertical)

        self.rules_table = make_table(
            ["المُقدِّم", "المُتْبَع", "الدعم", "الثقة", "الرفع", "الاستفادة", "الإقناع"], []
        )
        table_card = Card("قواعد الارتباط")
        table_card.add(self.rules_table)

        self.rules_chart_canvas = charts.canvas_for(charts.Figure(figsize=(6, 3)))
        self.rules_chart_card = Card("الثقة مقابل الرفع — حجم الدائرة يعكس الدعم")
        self.rules_chart_card.add(self.rules_chart_canvas)

        split.addWidget(table_card)
        split.addWidget(self.rules_chart_card)
        split.setSizes([420, 340])

        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.addWidget(split)
        return page

    def _charts_tab(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background:{brand.BG};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(14)

        top = QHBoxLayout()
        top.setSpacing(14)
        self.heat_card = Card("خريطة الحرارية للقوى (Lift)")
        self.heat_canvas = charts.canvas_for(charts.Figure(figsize=(6, 4)))
        self.heat_card.add(self.heat_canvas)
        self.net_card = Card("شبكة أقوى القواعد", "المُقدِّم يمينًا ← المُتْبَع يسارًا")
        self.net_canvas = charts.canvas_for(charts.Figure(figsize=(6, 4)))
        self.net_card.add(self.net_canvas)
        top.addWidget(self.heat_card, 1)
        top.addWidget(self.net_card, 1)
        layout.addLayout(top, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(14)
        self.freq_card = Card("أكثر المنتجات مبيعًا")
        self.freq_canvas = charts.canvas_for(charts.Figure(figsize=(6, 3)))
        self.freq_card.add(self.freq_canvas)
        self.basket_card = Card("توزيع حجم السلة")
        self.basket_canvas = charts.canvas_for(charts.Figure(figsize=(6, 3)))
        self.basket_card.add(self.basket_canvas)
        bottom.addWidget(self.freq_card, 1)
        bottom.addWidget(self.basket_card, 1)
        layout.addLayout(bottom, 1)
        return page

    def _summary_tab(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background:{brand.BG};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(14)

        tiles = QWidget()
        tile_row = QHBoxLayout(tiles)
        tile_row.setContentsMargins(0, 0, 0, 0)
        tile_row.setSpacing(14)
        self.sum_itemsets = StatTile("المتجهات المتكررة", "—", "", brand.PRIMARY)
        self.sum_rules = StatTile("قواعد الارتباط", "—", "", brand.TEAL)
        self.sum_strong = StatTile("قواعد رفع > 1.5", "—", "", brand.GREEN)
        self.sum_runtime = StatTile("زمن التنفيذ", "—", "بالثواني", brand.AMBER)
        for tile in (self.sum_itemsets, self.sum_rules, self.sum_strong, self.sum_runtime):
            tile_row.addWidget(tile)
        layout.addWidget(tiles)

        self.recommendations = QWidget()
        self.recommendations_layout = QVBoxLayout(self.recommendations)
        self.recommendations_layout.setContentsMargins(0, 0, 0, 0)
        self.recommendations_layout.setSpacing(12)
        layout.addWidget(self.recommendations, 1)
        return page

    # -- refresh ------------------------------------------------------------
    def _replace_canvas(self, card: Card, canvas_widget, figure):
        """Swap a matplotlib canvas inside a card for a freshly rendered one."""
        new_canvas = charts.canvas_for(figure)
        layout = card.body
        index = layout.indexOf(canvas_widget)
        layout.removeWidget(canvas_widget)
        canvas_widget.setParent(None)
        canvas_widget.deleteLater()
        layout.insertWidget(index, new_canvas)
        return new_canvas

    def refresh(self) -> None:
        st = self.controller.state
        if not st.has_results:
            self.sum_itemsets.set_value("—")
            self.sum_rules.set_value("—")
            self.sum_strong.set_value("—")
            self.sum_runtime.set_value("—")
            return

        result, rules = st.result, st.rules

        from PyQt6.QtGui import QStandardItem

        def fill(table, rows):
            model = table.model()
            model.setRowCount(0)
            for row in rows:
                items = []
                for value in row:
                    item = QStandardItem("" if value is None else str(value))
                    item.setEditable(False)
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    items.append(item)
                model.appendRow(items)

        fill(
            self.itemsets_table,
            [
                [it.label, it.size, f"{it.support:.4f}", f"{it.count:,}"]
                for it in result.itemsets
            ],
        )
        fill(
            self.rules_table,
            [
                [
                    rule.antecedent_label,
                    rule.consequent_label,
                    f"{rule.support:.4f}",
                    f"{rule.confidence:.4f}",
                    f"{rule.lift:.3f}",
                    f"{rule.leverage:.4f}",
                    f"{rule.conviction:.2f}",
                ]
                for rule in rules.rules
            ],
        )

        self.itemsets_chart_canvas = self._replace_canvas(
            self.itemsets_chart_card,
            self.itemsets_chart_canvas,
            charts.top_itemsets_chart(result.itemsets, top_n=10),
        )
        self.rules_chart_canvas = self._replace_canvas(
            self.rules_chart_card,
            self.rules_chart_canvas,
            charts.rules_scatter_chart(rules.rules),
        )
        self.heat_canvas = self._replace_canvas(
            self.heat_card,
            self.heat_canvas,
            charts.lift_heatmap_chart(rules.rules, st.dataset.items),
        )
        self.net_canvas = self._replace_canvas(
            self.net_card,
            self.net_canvas,
            charts.rules_network_chart(rules.rules),
        )
        self.freq_canvas = self._replace_canvas(
            self.freq_card,
            self.freq_canvas,
            charts.item_frequency_chart(st.dataset.item_counts, top_n=10),
        )
        self.basket_canvas = self._replace_canvas(
            self.basket_card,
            self.basket_canvas,
            charts.basket_size_chart(st.dataset.basket_sizes),
        )

        self.sum_itemsets.set_value(f"{len(result.itemsets):,}")
        self.sum_rules.set_value(f"{len(rules.rules):,}")
        strong = sum(1 for r in rules.rules if r.lift >= 1.5)
        self.sum_strong.set_value(f"{strong:,}")
        self.sum_runtime.set_value(f"{st.runtime:.2f}")

        self._build_recommendations(rules.rules)

    def _build_recommendations(self, rules) -> None:
        while self.recommendations_layout.count():
            item = self.recommendations_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        if not rules:
            empty = QLabel("لا توجد قواعد بعد — شغّل التحليل أولًا.")
            empty.setFont(brand.font(13))
            empty.setStyleSheet(f"color:{brand.MUTED}; background: transparent; border: none;")
            self.recommendations_layout.addWidget(empty)
            return

        card = Card("توصيات العرض والتسويق", "أقوى الروابط بين المنتجات")
        grid = QGridLayout()
        grid.setSpacing(12)
        for i, rule in enumerate(rules[:6]):
            tile = QFrame()
            tile.setObjectName("Tile")
            tile.setStyleSheet(
                f"""
                QFrame#Tile {{
                    background: #F8FAFC;
                    border: 1px solid {brand.BORDER};
                    border-radius: 12px;
                }}
                QFrame#Tile QLabel {{
                    background: transparent;
                    border: none;
                }}
                """
            )
            col = QVBoxLayout(tile)
            col.setContentsMargins(14, 12, 14, 12)
            col.setSpacing(5)

            title = QLabel(f"«{rule.antecedent_label}»  →  «{rule.consequent_label}»")
            title.setFont(brand.font(13, QFont.Weight.DemiBold))
            title.setStyleSheet(f"color:{brand.TEXT}; background: transparent; border: none;")
            title.setWordWrap(True)
            col.addWidget(title)

            body = QLabel(
                f"عند شراء العميل «{rule.antecedent_label}» كانت فرصة شراء "
                f"«{rule.consequent_label}» {rule.confidence:.0%} من المرات. "
                f"ضعهما معًا في الرف نفسه أو كعرض مقترح."
            )
            body.setFont(brand.font(12))
            body.setWordWrap(True)
            body.setStyleSheet(f"color:{brand.MUTED}; background: transparent; border: none;")
            col.addWidget(body)

            metrics = QLabel(
                f"دعم {rule.support:.1%}   •   ثقة {rule.confidence:.1%}   •   رفع {rule.lift:.2f}"
            )
            metrics.setFont(brand.font(11, QFont.Weight.DemiBold))
            metrics.setStyleSheet(f"color:{brand.PRIMARY}; background: transparent; border: none;")
            col.addWidget(metrics)

            grid.addWidget(tile, i // 2, i % 2)
        card.add_layout(grid)
        self.recommendations_layout.addWidget(card)


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------
class ExportPage(QWidget):
    def __init__(self, controller: Controller, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller
        outer, layout = page_scaffold()
        self.setLayout(layout)
        layout.addWidget(SectionTitle("التصدير", "صدّر نتائج التحليل لاستخدامها في التقارير"))
        layout.addWidget(self._exports_card())
        layout.addWidget(self._preview_card())
        layout.addStretch(1)
        self.refresh()

    def _exports_card(self) -> QWidget:
        card = Card("ملفات الإخراج")
        grid = QGridLayout()
        grid.setSpacing(14)

        specs = [
            (
                "المتجهات المتكررة",
                "كل مجموعة عناصر متكررة مع الدعم وعدد المعاملات.",
                "frequent_itemsets.csv",
                "export_itemsets_csv",
                brand.PRIMARY,
            ),
            (
                "قواعد الارتباط",
                "كل قاعدة مع الدعم والثقة والرفع والاستفادة والإقناع.",
                "association_rules.csv",
                "export_rules_csv",
                brand.TEAL,
            ),
            (
                "المعاملات المُطبَّعة",
                "نسخة مرتّبة من المعاملات بعد توحيد أسماء المنتجات.",
                "transactions_normalised.csv",
                "export_transactions_csv",
                brand.GREEN,
            ),
        ]
        for i, (title, desc, filename, method, color) in enumerate(specs):
            tile = QFrame()
            tile.setObjectName("Tile")
            tile.setStyleSheet(
                f"""
                QFrame#Tile {{
                    background: {brand.CARD};
                    border: 1px solid {brand.BORDER};
                    border-radius: 12px;
                }}
                QFrame#Tile QLabel {{
                    background: transparent;
                    border: none;
                }}
                """
            )
            col = QVBoxLayout(tile)
            col.setContentsMargins(16, 14, 16, 14)
            col.setSpacing(6)

            head = QHBoxLayout()
            icon = IconWidgetHost("export", color)
            icon.setFixedSize(18, 18)
            head.addWidget(icon)
            name = QLabel(title)
            name.setFont(brand.font(14, QFont.Weight.DemiBold))
            name.setStyleSheet(f"color:{brand.TEXT}; background: transparent; border: none;")
            head.addWidget(name)
            head.addStretch(1)
            col.addLayout(head)

            info = QLabel(desc)
            info.setFont(brand.font(12))
            info.setWordWrap(True)
            info.setStyleSheet(f"color:{brand.MUTED}; background: transparent; border: none;")
            col.addWidget(info)

            fname = QLabel(filename)
            fname.setFont(brand.font(11))
            fname.setStyleSheet(f"color:{brand.MUTED_LIGHT}; background: transparent; border: none;")
            col.addWidget(fname)

            button = PrimaryButton("تصدير", "export")
            button.setMinimumHeight(38)
            button.clicked.connect(lambda _=False, m=method: self._do_export(m))
            col.addWidget(button)
            grid.addWidget(tile, i // 3, i % 3)

        card.add_layout(grid)
        self.export_status = QLabel("")
        self.export_status.setFont(brand.font(12))
        self.export_status.setStyleSheet(f"color:{brand.GREEN}; background: transparent; border: none;")
        card.add(self.export_status)
        return card

    def _preview_card(self) -> QWidget:
        card = Card("معاينة قواعد الارتباط", "أول 12 قاعدة بصيغة ملف الإخراج")
        self.preview_table = make_table(
            ["المُقدِّم", "المُتْبَع", "الدعم", "الثقة", "الرفع"], []
        )
        self.preview_table.setMinimumHeight(200)
        card.add(self.preview_table)
        return card

    def _do_export(self, method_name: str) -> None:
        method = getattr(self.controller, method_name)
        directory = QFileDialog.getExistingDirectory(self, "اختر مجلد التصدير")
        if not directory:
            return
        path = method(directory)
        if path:
            self.export_status.setText(f"تم حفظ الملف: {path}")
        else:
            self.export_status.setText("لا توجد بيانات للتصدير بعد.")

    def refresh(self) -> None:
        st = self.controller.state
        from PyQt6.QtGui import QStandardItem

        model = self.preview_table.model()
        model.setRowCount(0)
        if st.has_results:
            for rule in st.rules.rules[:12]:
                values = [
                    rule.antecedent_label,
                    rule.consequent_label,
                    f"{rule.support:.4f}",
                    f"{rule.confidence:.4f}",
                    f"{rule.lift:.3f}",
                ]
                items = []
                for value in values:
                    item = QStandardItem(value)
                    item.setEditable(False)
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                    items.append(item)
                model.appendRow(items)


# --------------------------------------------------------------------------
# About
# --------------------------------------------------------------------------
class AboutPage(QWidget):
    def __init__(self, controller: Controller, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller
        outer, layout = page_scaffold()
        self.setLayout(layout)
        layout.addWidget(SectionTitle("عن الأداة", "الهوية، والخوارزمية، ومؤشرات القياس"))
        layout.addWidget(self._identity_card())
        layout.addWidget(self._algorithm_card())
        layout.addWidget(self._metrics_card())
        layout.addStretch(1)

    def _identity_card(self) -> QWidget:
        card = Card()
        row = QHBoxLayout()
        row.setSpacing(20)

        mark = LogoWidget(72)
        row.addWidget(mark)

        col = QVBoxLayout()
        col.setSpacing(4)
        title = QLabel("سَلّة")
        title.setFont(brand.font(26, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{brand.TEXT}; background: transparent; border: none;")
        col.addWidget(title)
        tagline = QLabel("منصّة تحليل سلة المشتريات — متجر المشتريات يبيع منتجات، والأداة تكتشف الروابط بينها.")
        tagline.setFont(brand.font(13))
        tagline.setWordWrap(True)
        tagline.setStyleSheet(f"color:{brand.MUTED}; background: transparent; border: none;")
        col.addWidget(tagline)

        identity = QLabel(
            "الهوية البصرية مبنية على ثلاث ركائز: أزرق كحلي يرمز للبيانات، "
            "وأزرق سماوي يرمز للوضوح، وسلة تحمل أعمدة صاعدة ترمز للنمو."
        )
        identity.setFont(brand.font(12))
        identity.setWordWrap(True)
        identity.setStyleSheet(f"color:{brand.TEXT_SOFT}; background: transparent; border: none;")
        col.addWidget(identity)
        row.addLayout(col, 1)
        card.add_layout(row)
        return card

    def _algorithm_card(self) -> QWidget:
        card = Card("كيف تعمل خوارزمية Apriori", "أربع مراحل داخل الأداة")
        steps = [
            ("L₁", "حساب دعم كل منتج على حدة، واستبعاد ما دون الحد الأدنى."),
            ("Cₖ", "توليد المرشحين بدمج المجموعات المتكررة السابقة."),
            ("Prune", "قصّ أي مرشح لا تتكرّر كل مجموعاته الجزئية (خاصية Apriori)."),
            ("Rules", "اشتقاق القواعد بحساب الثقة والرفع لكل تقسيم للمجموعة."),
        ]
        grid = QGridLayout()
        grid.setSpacing(12)
        for i, (tag, text) in enumerate(steps):
            tile = QFrame()
            tile.setObjectName("Tile")
            tile.setStyleSheet(
                f"""
                QFrame#Tile {{
                    background: {brand.PRIMARY_SOFT};
                    border: 1px solid {brand.PRIMARY_BORDER};
                    border-radius: 10px;
                }}
                QFrame#Tile QLabel {{
                    background: transparent;
                    border: none;
                }}
                """
            )
            col = QVBoxLayout(tile)
            col.setContentsMargins(14, 12, 14, 12)
            col.setSpacing(4)
            tag_label = QLabel(tag)
            tag_label.setFont(brand.font(15, QFont.Weight.Bold))
            tag_label.setStyleSheet(f"color:{brand.PRIMARY}; background: transparent; border: none;")
            col.addWidget(tag_label)
            text_label = QLabel(text)
            text_label.setFont(brand.font(12))
            text_label.setWordWrap(True)
            text_label.setStyleSheet(f"color:{brand.TEXT_SOFT}; background: transparent; border: none;")
            col.addWidget(text_label)
            grid.addWidget(tile, i // 2, i % 2)
        card.add_layout(grid)
        return card

    def _metrics_card(self) -> QWidget:
        card = Card("مؤشرات القياس", "معنى كل رقم يظهر في النتائج")
        table = make_table(
            ["المؤشر", "الرمز", "المعنى"],
            [
                ["الدعم", "support", "نسبة المعاملات التي تحتوي المجموعة كاملة."],
                ["الثقة", "confidence", "احتمال شراء المنتج المتْبع عندما يُشترى المُقدِّم."],
                ["الرفع", "lift", "أكثر من ضعف احتمال الشراء عمّا كان لو كان عشوائيًا."],
                ["الاستفادة", "leverage", "نسبة التحسّن الحقيقي عن العشوائية."],
                ["الإقناع", "conviction", "قوة الدليل ضد احتمالات الشراء العشوائي."],
            ],
        )
        table.setMinimumHeight(220)
        table.setWordWrap(True)
        table.verticalHeader().setDefaultSectionSize(38)
        card.add(table)
        return card
