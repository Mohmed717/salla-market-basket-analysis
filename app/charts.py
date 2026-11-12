"""Matplotlib charts themed to the Salla brand, embeddable in Qt."""

from __future__ import annotations

import math
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("QtAgg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch

from . import brand
from mba.apriori import FrequentItemset
from mba.rules import AssociationRule

try:  # pragma: no cover - optional dependency
    import arabic_reshaper
    from bidi.algorithm import get_display

    _reshaper = arabic_reshaper.ArabicReshaper(
        configuration={"delete_harakat": False, "support_ligatures": False}
    )

    def ar(text: str) -> str:
        """Shape and reorder Arabic text so matplotlib renders it correctly."""
        if not text:
            return ""
        try:
            return get_display(_reshaper.reshape(str(text)))
        except Exception:  # pragma: no cover - defensive
            return str(text)

except ImportError:  # pragma: no cover

    def ar(text: str) -> str:
        return str(text)


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": [brand.FONT_FAMILY, brand.FONT_FALLBACK, "DejaVu Sans"],
            "font.size": 10,
            "axes.edgecolor": brand.BORDER_STRONG,
            "axes.labelcolor": brand.TEXT_SOFT,
            "axes.titlecolor": brand.TEXT,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "text.color": brand.TEXT,
            "xtick.color": brand.MUTED,
            "ytick.color": brand.MUTED,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "grid.color": "#EDF2F7",
            "grid.linewidth": 1.0,
            "figure.autolayout": False,
        }
    )


configure_style()


def _clean_axes(ax, grid_axis: str = "y") -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(brand.BORDER_STRONG)
    ax.spines["bottom"].set_color(brand.BORDER_STRONG)
    ax.grid(True, axis=grid_axis, linestyle="-", alpha=0.9, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def _canvas(fig: Figure) -> FigureCanvasQTAgg:
    canvas = FigureCanvasQTAgg(fig)
    canvas.setStyleSheet("background: transparent;")
    return canvas


def _shorten(text: str, limit: int = 18) -> str:
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _chart_label(text: str, limit: int = 14) -> str:
    """Readable RTL label: shorten each item and join with an Arabic comma."""
    parts = [_shorten(part.strip(), limit) for part in str(text).split("|") if part.strip()]
    return "، ".join(parts) if parts else str(text)


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------
def top_itemsets_chart(
    itemsets: Sequence[FrequentItemset], top_n: int = 10, horizontal: bool = False
) -> Figure:
    """Bar chart of the most frequent itemsets."""
    data = list(itemsets)[:top_n]
    fig = Figure(figsize=(6.4, 3.4), dpi=100)
    ax = fig.add_subplot(111)
    if not data:
        ax.text(0.5, 0.5, "لا توجد نتائج", ha="center", va="center", color=brand.MUTED)
        ax.axis("off")
        return fig

    labels = [_chart_label(it.label, 16) for it in data]
    values = [it.support for it in data]
    colors = [brand.CHART_SERIES[i % len(brand.CHART_SERIES)] for i in range(len(data))]

    if horizontal:
        bars = ax.barh(labels, values, color=colors, height=0.62, zorder=3)
        ax.invert_yaxis()
        ax.set_xlim(0, max(values) * 1.18)
        _clean_axes(ax, "x")
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_width() + max(values) * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{value:.3f}",
                va="center",
                ha="left",
                fontsize=9,
                color=brand.TEXT_SOFT,
            )
    else:
        bars = ax.bar(labels, values, color=colors, width=0.62, zorder=3)
        ax.set_ylim(0, max(values) * 1.2)
        _clean_axes(ax, "y")
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values) * 0.03,
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
                color=brand.TEXT_SOFT,
            )
        for label in ax.get_xticklabels():
            label.set_rotation(18)
            label.set_ha("right")
    fig.tight_layout(pad=1.1)
    return fig


def item_frequency_chart(item_counts, top_n: int = 12) -> Figure:
    """Horizontal bars of the most frequently bought products."""
    pairs = sorted(item_counts.items(), key=lambda kv: -kv[1])[:top_n]
    fig = Figure(figsize=(6.4, 3.8), dpi=100)
    ax = fig.add_subplot(111)
    if not pairs:
        ax.axis("off")
        return fig
    labels = [ar(_chart_label(name, 16)) for name, _ in pairs]
    values = [count for _, count in pairs]
    colors = [brand.CHART_SERIES[i % len(brand.CHART_SERIES)] for i in range(len(values))]
    bars = ax.barh(labels, values, color=colors, height=0.64, zorder=3)
    ax.invert_yaxis()
    ax.set_xlim(0, max(values) * 1.16)
    _clean_axes(ax, "x")
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_width() + max(values) * 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{value:,}",
            va="center",
            fontsize=9,
            color=brand.TEXT_SOFT,
        )
    fig.tight_layout(pad=1.1)
    return fig


def support_by_level_chart(levels: dict[int, list[FrequentItemset]]) -> Figure:
    """How many frequent itemsets exist at each size."""
    fig = Figure(figsize=(5.2, 3.0), dpi=100)
    ax = fig.add_subplot(111)
    if not levels:
        ax.axis("off")
        return fig
    sizes = sorted(levels)
    counts = [len(levels[s]) for s in sizes]
    labels = [f"{s} عناصر" for s in sizes]
    bars = ax.bar(labels, counts, color=brand.PRIMARY, width=0.55, zorder=3)
    ax.set_ylim(0, max(counts) * 1.22)
    _clean_axes(ax, "y")
    for bar, value in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(counts) * 0.03,
            f"{value:,}",
            ha="center",
            fontsize=9,
            color=brand.TEXT_SOFT,
        )
    fig.tight_layout(pad=1.1)
    return fig


def rules_scatter_chart(rules: Sequence[AssociationRule], top_n: int = 200) -> Figure:
    """Confidence versus lift, bubble size proportional to support."""
    fig = Figure(figsize=(6.4, 3.6), dpi=100)
    ax = fig.add_subplot(111)
    data = list(rules)[:top_n]
    if not data:
        ax.text(0.5, 0.5, "لا توجد قواعد", ha="center", va="center", color=brand.MUTED)
        ax.axis("off")
        return fig

    x = [r.confidence for r in data]
    y = [min(r.lift, 6.0) for r in data]
    sizes = [max(28, r.support * 4200) for r in data]
    colors = [
        brand.CHART_SERIES[int(min(r.lift, 6.0)) % len(brand.CHART_SERIES)] for r in data
    ]

    ax.scatter(x, y, s=sizes, c=colors, alpha=0.72, edgecolors="white", linewidths=1.4, zorder=3)
    ax.axhline(1.0, color=brand.ROSE, linestyle="--", linewidth=1.2, alpha=0.8, zorder=2)
    ax.text(
        0.02,
        1.02,
        "lift = 1 (ارتباط عشوائي)",
        transform=ax.get_yaxis_transform(),
        color=brand.ROSE,
        fontsize=9,
    )
    _clean_axes(ax, "both")
    ax.set_xlabel("الثقة (Confidence)")
    ax.set_ylabel("الرفع (Lift)")
    fig.tight_layout(pad=1.1)
    return fig


def lift_heatmap_chart(
    rules: Sequence[AssociationRule], items: Sequence[str], max_items: int = 12
) -> Figure:
    """Heatmap of the strongest lift between every pair of products."""
    fig = Figure(figsize=(7.0, 5.4), dpi=100)
    ax = fig.add_subplot(111)

    # Prefer the products that actually take part in a rule so the matrix is
    # dense and readable instead of mostly empty.
    participating: dict[str, float] = {}
    for rule in rules:
        if len(rule.antecedent) != 1 or len(rule.consequent) != 1:
            continue
        a = next(iter(rule.antecedent))
        b = next(iter(rule.consequent))
        participating[a] = max(participating.get(a, 0.0), rule.lift)
        participating[b] = max(participating.get(b, 0.0), rule.lift)

    if participating:
        top_items = [
            name
            for name, _ in sorted(participating.items(), key=lambda kv: -kv[1])[:max_items]
        ]
    else:
        top_items = list(items)[:max_items]

    index = {name: i for i, name in enumerate(top_items)}
    size = len(top_items)
    matrix = [[float("nan")] * size for _ in range(size)]

    for rule in rules:
        if len(rule.antecedent) != 1 or len(rule.consequent) != 1:
            continue
        a = next(iter(rule.antecedent))
        b = next(iter(rule.consequent))
        if a not in index or b not in index:
            continue
        i, j = index[a], index[b]
        value = rule.lift
        if math.isnan(matrix[i][j]) or value > matrix[i][j]:
            matrix[i][j] = value
            matrix[j][i] = value

    if size == 0:
        ax.axis("off")
        return fig

    import numpy as np

    arr = np.array(matrix, dtype=float)
    masked = np.ma.masked_invalid(arr)
    cmap = matplotlib.colormaps["Blues"].copy().with_extremes(bad="#F1F5F9")
    im = ax.imshow(masked, cmap=cmap, aspect="auto", vmin=1.0)
    ax.set_xticks(range(size))
    ax.set_yticks(range(size))
    ax.set_xticklabels(
        [ar(_chart_label(t, 12)) for t in top_items], rotation=42, ha="right", fontsize=8
    )
    ax.set_yticklabels([ar(_chart_label(t, 14)) for t in top_items], fontsize=8)
    ax.set_xticks(np.arange(-0.5, size, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, size, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.6)
    ax.tick_params(which="minor", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
    cbar.set_label("Lift", color=brand.TEXT_SOFT, fontsize=9)
    cbar.outline.set_visible(False)
    cbar.ax.tick_params(length=0, labelsize=8)
    fig.subplots_adjust(left=0.14, right=0.92, top=0.96, bottom=0.26)
    return fig


def rules_network_chart(rules: Sequence[AssociationRule], top_n: int = 10) -> Figure:
    """Bipartite map of the strongest rules: antecedents on the right, consequents on the left."""
    fig = Figure(figsize=(7.0, 5.2), dpi=100)
    ax = fig.add_subplot(111)
    data = list(rules)[:top_n]
    if not data:
        ax.text(0.5, 0.5, "لا توجد قواعد", ha="center", va="center", color=brand.MUTED)
        ax.axis("off")
        return fig

    antecedents: list[str] = []
    consequents: list[str] = []
    for rule in data:
        if rule.antecedent_label not in antecedents:
            antecedents.append(rule.antecedent_label)
        if rule.consequent_label not in consequents:
            consequents.append(rule.consequent_label)

    def positions(nodes: list[str], x: float) -> dict[str, tuple[float, float]]:
        if not nodes:
            return {}
        step = 1.0 / (len(nodes) + 1)
        return {name: (x, 1.0 - step * (i + 1)) for i, name in enumerate(nodes)}

    left = positions(consequents, 0.34)
    right = positions(antecedents, 0.66)

    max_lift = max((r.lift for r in data), default=1.0)
    for rule in data:
        x0, y0 = right[rule.antecedent_label]
        x1, y1 = left[rule.consequent_label]
        width = 0.8 + 3.4 * (rule.lift / max(max_lift, 1.0))
        colour = brand.CHART_SERIES[int(min(rule.lift, 7.0)) % len(brand.CHART_SERIES)]
        ax.annotate(
            "",
            xy=(x1 + 0.035, y1),
            xytext=(x0 - 0.035, y0),
            arrowprops=dict(
                arrowstyle="-|>",
                color=colour,
                alpha=0.55,
                linewidth=width,
                shrinkA=2,
                shrinkB=2,
                connectionstyle="arc3,rad=0.16",
            ),
        )

    for name, (x, y) in left.items():
        ax.scatter([x], [y], s=190, color=brand.TEAL, zorder=4, edgecolors="white", linewidths=1.6)
        ax.text(
            x - 0.02,
            y,
            ar(_chart_label(name, 14)),
            ha="right",
            va="center",
            fontsize=8.5,
            color=brand.TEXT,
            zorder=5,
        )

    for name, (x, y) in right.items():
        ax.scatter([x], [y], s=190, color=brand.PRIMARY, zorder=4, edgecolors="white", linewidths=1.6)
        ax.text(
            x + 0.02,
            y,
            ar(_chart_label(name, 14)),
            ha="left",
            va="center",
            fontsize=8.5,
            color=brand.TEXT,
            zorder=5,
        )

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(-0.02, 1.02)
    ax.set_axis_off()
    fig.subplots_adjust(left=0.02, right=0.98, top=0.96, bottom=0.04)
    return fig


def basket_size_chart(sizes: Sequence[int]) -> Figure:
    """Distribution of basket sizes."""
    fig = Figure(figsize=(5.4, 3.0), dpi=100)
    ax = fig.add_subplot(111)
    if not sizes:
        ax.axis("off")
        return fig
    buckets: dict[int, int] = {}
    for size in sizes:
        key = size if size <= 6 else 7
        buckets[key] = buckets.get(key, 0) + 1
    labels = [f"{k}" if k < 7 else "7+" for k in sorted(buckets)]
    values = [buckets[k] for k in sorted(buckets)]
    bars = ax.bar(labels, values, color=brand.TEAL, width=0.58, zorder=3)
    ax.set_ylim(0, max(values) * 1.2)
    _clean_axes(ax, "y")
    ax.set_xlabel("عدد المنتجات في السلة")
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(values) * 0.03,
            f"{value:,}",
            ha="center",
            fontsize=9,
            color=brand.TEXT_SOFT,
        )
    fig.tight_layout(pad=1.1)
    return fig


def canvas_for(fig: Figure) -> FigureCanvasQTAgg:
    """Wrap a figure into a Qt canvas."""
    return _canvas(fig)
