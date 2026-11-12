#!/usr/bin/env python3
"""Command line interface for the Salla market basket analysis engine.

    python3 cli.py data/transactions.csv --min-support 0.1 --min-confidence 0.6
    python3 cli.py data/transactions.csv --outdir exports --top 20
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mba.apriori import apriori
from mba.loader import load_csv
from mba.rules import generate_rules


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="salla",
        description="تحليل سلة المشتريات باستخدام خوارزمية Apriori.",
    )
    parser.add_argument("input", help="مسار ملف المعاملات CSV.")
    parser.add_argument(
        "--min-support", type=float, default=0.10, help="الحد الأدنى للدعم (0-1)."
    )
    parser.add_argument(
        "--min-confidence", type=float, default=0.60, help="الحد الأدنى للثقة (0-1)."
    )
    parser.add_argument(
        "--min-lift", type=float, default=1.0, help="الحد الأدنى للرفع (default 1.0)."
    )
    parser.add_argument(
        "--max-len", type=int, default=3, help="أقصى طول للمجموعة المتكررة."
    )
    parser.add_argument("--top", type=int, default=15, help="عدد النتائج المعروضة.")
    parser.add_argument(
        "--outdir", default="exports", help="مجلد إخراج ملفات CSV."
    )
    parser.add_argument(
        "--no-export", action="store_true", help="عدم كتابة ملفات الإخراج."
    )
    parser.add_argument(
        "--encoding", default="utf-8", help="ترميز ملف الإدخال."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    path = Path(args.input)
    if not path.exists():
        print(f"الملف غير موجود: {path}", file=sys.stderr)
        return 2

    dataset = load_csv(path, encoding=args.encoding)
    if dataset.n_transactions == 0:
        print("لم يتم العثور على معاملات صالحة في الملف.", file=sys.stderr)
        for warning in dataset.warnings:
            print(f"  {warning}", file=sys.stderr)
        return 1

    print("─" * 68)
    print("  سَلّة — تحليل سلة المشتريات")
    print("─" * 68)
    print(f"  الملف            : {dataset.source_name}")
    print(f"  الصيغة           : {dataset.format}")
    print(f"  المعاملات        : {dataset.n_transactions:,}")
    print(f"  المنتجات الفريدة : {dataset.n_items:,}")
    print(f"  متوسط حجم السلة  : {dataset.avg_basket_size:.2f}")
    print("─" * 68)

    started = time.perf_counter()
    result = apriori(
        dataset.transactions,
        min_support=args.min_support,
        max_len=args.max_len,
    )
    rules = generate_rules(
        result,
        min_confidence=args.min_confidence,
        min_lift=args.min_lift,
    )
    elapsed = time.perf_counter() - started

    print(f"  زمن التنفيذ      : {elapsed:.3f} ثانية")
    print(f"  المتجهات المتكررة : {len(result.itemsets):,}")
    print(f"  قواعد الارتباط   : {len(rules.rules):,}")
    print("─" * 68)

    print("\n  أعلى المتجهات المتكررة:")
    print(f"  {'المجموعة':<42} {'الدعم':>8} {'العدد':>7}")
    for itemset in result.itemsets[: args.top]:
        label = itemset.label
        print(f"  {label[:40]:<42} {itemset.support:>8.4f} {itemset.count:>7,}")

    print("\n  أقوى قواعد الارتباط:")
    print(
        f"  {'المُقدِّم':<22} {'→':^2} {'المُتْبَع':<22} "
        f"{'دعم':>7} {'ثقة':>7} {'رفع':>7}"
    )
    for rule in rules.rules[: args.top]:
        print(
            f"  {rule.antecedent_label[:20]:<22} → {rule.consequent_label[:20]:<22} "
            f"{rule.support:>7.4f} {rule.confidence:>7.4f} {rule.lift:>7.3f}"
        )

    if not args.no_export:
        outdir = Path(args.outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        itemsets_path = outdir / "frequent_itemsets.csv"
        with itemsets_path.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(["itemset", "size", "support", "count"])
            for itemset in result.itemsets:
                writer.writerow(
                    [itemset.label, itemset.size, round(itemset.support, 6), itemset.count]
                )

        rules_path = outdir / "association_rules.csv"
        with rules_path.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                [
                    "antecedent",
                    "consequent",
                    "support",
                    "confidence",
                    "lift",
                    "leverage",
                    "conviction",
                    "count",
                ]
            )
            for rule in rules.rules:
                writer.writerow(
                    [
                        rule.antecedent_label,
                        rule.consequent_label,
                        round(rule.support, 6),
                        round(rule.confidence, 6),
                        round(rule.lift, 6),
                        round(rule.leverage, 6),
                        round(rule.conviction, 6),
                        rule.count,
                    ]
                )
        print(f"\n  تم حفظ النتائج في: {outdir.resolve()}")
        print(f"    • {itemsets_path.name}")
        print(f"    • {rules_path.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
