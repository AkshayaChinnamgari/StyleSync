import argparse
import csv
import json
import os
import sys
from typing import Dict, List, Tuple

# Ensure backend is on sys.path
SCRIPT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.append(BACKEND_DIR)

from utils.classify import classify_garment
from utils.image_utils import get_dominant_color


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    hex_color = hex_color.strip().lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def srgb_to_linear(c: float) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb_to_xyz(r: int, g: int, b: int) -> Tuple[float, float, float]:
    r_lin = srgb_to_linear(r)
    g_lin = srgb_to_linear(g)
    b_lin = srgb_to_linear(b)

    # D65 reference white
    x = r_lin * 0.4124 + g_lin * 0.3576 + b_lin * 0.1805
    y = r_lin * 0.2126 + g_lin * 0.7152 + b_lin * 0.0722
    z = r_lin * 0.0193 + g_lin * 0.1192 + b_lin * 0.9505
    return x, y, z


def xyz_to_lab(x: float, y: float, z: float) -> Tuple[float, float, float]:
    # D65 reference white
    x_ref, y_ref, z_ref = 0.95047, 1.00000, 1.08883
    x /= x_ref
    y /= y_ref
    z /= z_ref

    def f(t: float) -> float:
        return t ** (1/3) if t > 0.008856 else (7.787 * t + 16/116)

    fx, fy, fz = f(x), f(y), f(z)
    l = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    return l, a, b


def rgb_to_lab(r: int, g: int, b: int) -> Tuple[float, float, float]:
    x, y, z = rgb_to_xyz(r, g, b)
    return xyz_to_lab(x, y, z)


def delta_e(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    return ((lab1[0] - lab2[0]) ** 2 + (lab1[1] - lab2[1]) ** 2 + (lab1[2] - lab2[2]) ** 2) ** 0.5


def compute_classification_metrics(y_true: List[str], y_pred: List[str]) -> Dict[str, float]:
    labels = sorted(set(y_true) | set(y_pred))
    label_to_idx = {label: i for i, label in enumerate(labels)}

    tp = {label: 0 for label in labels}
    fp = {label: 0 for label in labels}
    fn = {label: 0 for label in labels}

    for t, p in zip(y_true, y_pred):
        if t == p:
            tp[t] += 1
        else:
            fp[p] += 1
            fn[t] += 1

    def safe_div(n: float, d: float) -> float:
        return n / d if d else 0.0

    precision = {}
    recall = {}
    f1 = {}
    support = {}

    for label in labels:
        precision[label] = safe_div(tp[label], tp[label] + fp[label])
        recall[label] = safe_div(tp[label], tp[label] + fn[label])
        f1[label] = safe_div(2 * precision[label] * recall[label], precision[label] + recall[label])
        support[label] = tp[label] + fn[label]

    total = sum(support.values())
    macro_precision = sum(precision.values()) / len(labels) if labels else 0.0
    macro_recall = sum(recall.values()) / len(labels) if labels else 0.0
    macro_f1 = sum(f1.values()) / len(labels) if labels else 0.0

    weighted_precision = sum(precision[l] * support[l] for l in labels) / total if total else 0.0
    weighted_recall = sum(recall[l] * support[l] for l in labels) / total if total else 0.0
    weighted_f1 = sum(f1[l] * support[l] for l in labels) / total if total else 0.0

    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true) if y_true else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_precision": round(weighted_precision, 4),
        "weighted_recall": round(weighted_recall, 4),
        "weighted_f1": round(weighted_f1, 4),
        "labels": labels,
    }


def evaluate(images_dir: str, labels_csv: str, out_path: str, limit: int = 0) -> None:
    y_true = []
    y_pred = []

    color_exact_matches = 0
    color_total = 0
    rgb_distances = []
    delta_e_values = []

    with open(labels_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if limit and limit > 0:
        rows = rows[:limit]

    for row in rows:
        filename = row.get("filename", "").strip()
        true_category = row.get("true_category", "").strip().lower()
        true_color_hex = row.get("true_color_hex", "").strip()

        if not filename or not true_category:
            continue

        image_path = os.path.join(images_dir, filename)
        if not os.path.exists(image_path):
            print(f"[SKIP] Missing image: {image_path}")
            continue

        pred_category = classify_garment(image_path)
        y_true.append(true_category)
        y_pred.append(pred_category.lower() if pred_category else "")

        if true_color_hex:
            pred_color = get_dominant_color(image_path)
            color_total += 1
            if pred_color.lower() == true_color_hex.lower():
                color_exact_matches += 1

            try:
                r1, g1, b1 = hex_to_rgb(pred_color)
                r2, g2, b2 = hex_to_rgb(true_color_hex)
                rgb_dist = ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5
                rgb_distances.append(rgb_dist)

                lab1 = rgb_to_lab(r1, g1, b1)
                lab2 = rgb_to_lab(r2, g2, b2)
                delta_e_values.append(delta_e(lab1, lab2))
            except Exception as e:
                print(f"[WARN] Color error calc failed for {filename}: {e}")

    cls_metrics = compute_classification_metrics(y_true, y_pred)

    color_metrics = {
        "hex_match_rate": round(color_exact_matches / color_total, 4) if color_total else 0.0,
        "mean_rgb_distance": round(sum(rgb_distances) / len(rgb_distances), 4) if rgb_distances else 0.0,
        "mean_delta_e": round(sum(delta_e_values) / len(delta_e_values), 4) if delta_e_values else 0.0,
        "color_samples": color_total,
    }

    metrics = {
        "samples": len(y_true),
        "classification": cls_metrics,
        "color": color_metrics,
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("\n=== Evaluation Summary ===")
    print(f"Samples: {metrics['samples']}")
    print(f"Accuracy: {cls_metrics['accuracy']}")
    print(f"Macro F1: {cls_metrics['macro_f1']}")
    print(f"Weighted F1: {cls_metrics['weighted_f1']}")
    print(f"HEX match rate: {color_metrics['hex_match_rate']}")
    print(f"Mean ΔE: {color_metrics['mean_delta_e']}")
    print(f"Saved: {out_path}\n")


def main():
    parser = argparse.ArgumentParser(description="Evaluate StyleSync garment classification + color extraction.")
    parser.add_argument("--images-dir", required=True, help="Folder with test images")
    parser.add_argument("--labels", required=True, help="CSV with filename,true_category,true_color_hex")
    parser.add_argument("--out", default=os.path.join(SCRIPT_DIR, "metrics.json"), help="Output JSON path")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of rows")
    args = parser.parse_args()

    evaluate(args.images_dir, args.labels, args.out, args.limit)


if __name__ == "__main__":
    main()
