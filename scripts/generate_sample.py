"""Generate a realistic grocery transactions CSV for demo/testing.

    python -m scripts.generate_sample --out data/sample_transactions.csv --rows 1500
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

CATEGORIES: dict[str, list[str]] = {
    "ألبان": ["حليب طازج", "لبن زبادي", "جبن شيدر", "زبدة", "قشطة", "جبنة بيضاء"],
    "مخبوزات": ["خبز عربي", "خبز توست", "كرواسون", "بقسماط", "ميني معجنات"],
    "خضار وفواكه": [
        "طماطم",
        "بطاطس",
        "بصل",
        "خيار",
        "تفاح",
        "برتقال",
        "موز",
        "ليمون",
        "جزر",
    ],
    "لحوم ودواجن": [
        "دجاج طازج",
        "لحم مفروم",
        "لحم غنم",
        "كبد",
        "سمك بلطي",
    ],
    "بقالة": [
        "أرز مصري",
        "سكر",
        "زيت زيتون",
        "مكرونة",
        "شاي",
        "ملح",
        "قهوة عربية",
        "عدس",
    ],
    "منظفات": ["مسحوق غسيل", "سائل جلي", "منظف أرضيات", "معطر ملابس"],
    "حلويات": ["شوكولاتة", "بسكويت", "عسل", "مكسرات مشكلة", "علكة"],
    "مشروبات": ["عصير برتقال", "مشروب غازي", "مياه معدنية", "عصير مانجو"],
}

# Anchor products: buying them strongly pulls the attached products along.
ATTACHMENTS: dict[str, list[tuple[str, float]]] = {
    "حليب طازج": [("خبز توست", 0.80), ("شوكولاتة", 0.58), ("عسل", 0.64)],
    "قشطة": [("عسل", 0.74), ("مكسرات مشكلة", 0.50)],
    "خبز عربي": [("طماطم", 0.60), ("زبدة", 0.68), ("شاي", 0.64)],
    "دجاج طازج": [("أرز مصري", 0.86), ("خيار", 0.62), ("زيت زيتون", 0.54)],
    "لحم مفروم": [("أرز مصري", 0.74), ("صلصة طماطم", 0.68), ("معكرونة", 0.46)],
    "شوكولاتة": [("عسل", 0.60), ("مكسرات مشكلة", 0.64)],
    "شاي": [("سكر", 0.90), ("بسكويت", 0.60)],
    "قهوة عربية": [("سكر", 0.72), ("حليب طازج", 0.56)],
    "أرز مصري": [("دجاج طازج", 0.60), ("زيت زيتون", 0.64)],
    "مسحوق غسيل": [("سائل جلي", 0.86), ("معطر ملابس", 0.56)],
    "لبن زبادي": [("فواكه مجففة", 0.60)],
}

ALL_ITEMS = sorted({item for items in CATEGORIES.values() for item in items})


def build_rows(n_rows: int, seed: int = 20260211) -> list[list[str]]:
    rng = random.Random(seed)
    rows: list[list[str]] = []
    for t in range(1, n_rows + 1):
        basket: set[str] = set()

        # 1-2 anchor products that drive the basket.
        anchors = rng.sample(list(ATTACHMENTS.keys()), k=rng.randint(1, 2))
        for anchor in anchors:
            basket.add(anchor)
            for partner, probability in ATTACHMENTS[anchor]:
                if rng.random() < probability:
                    basket.add(partner)

        # 0-2 independent fill-in items.
        for _ in range(rng.randint(0, 2)):
            basket.add(rng.choice(ALL_ITEMS))

        if not basket:
            basket.add(rng.choice(ALL_ITEMS))

        items = sorted(basket)
        rows.append([f"T{t:05d}", "; ".join(items), f"{rng.randint(1, 6)}", f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"])

    return rows


def write_csv(path: Path, rows: list[list[str]], fmt: str = "basket") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if fmt == "basket":
            writer.writerow(["transaction_id", "items", "quantity", "date"])
            for row in rows:
                writer.writerow(row)
        elif fmt == "long":
            writer.writerow(["transaction_id", "item", "date"])
            for row in rows:
                for item in row[1].split("; "):
                    writer.writerow([row[0], item, row[3]])
        else:  # wide
            items = sorted({i for row in rows for i in row[1].split("; ")})
            writer.writerow(["transaction_id"] + items)
            for row in rows:
                basket = set(row[1].split("; "))
                writer.writerow([row[0]] + [1 if i in basket else 0 for i in items])


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a sample transactions CSV.")
    parser.add_argument("--out", default="data/sample_transactions.csv")
    parser.add_argument("--rows", type=int, default=1500)
    parser.add_argument("--seed", type=int, default=20260211)
    parser.add_argument(
        "--format",
        choices=["basket", "long", "wide"],
        default="basket",
        help="Transaction layout to write.",
    )
    args = parser.parse_args()

    rows = build_rows(args.rows, args.seed)
    out = Path(args.out)
    write_csv(out, rows, args.format)
    print(f"Wrote {len(rows)} transactions to {out} ({args.format} format)")


if __name__ == "__main__":
    main()
