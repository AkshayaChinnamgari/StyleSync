import argparse
import csv
import os
import shutil


def suggest_category(name: str) -> str:
    n = name.lower()
    keyword_map = [
        ("kurti", "kurta"),
        ("kurta", "kurta"),
        ("dress", "dress"),
        ("skirt", "skirt"),
        ("pant", "pants"),
        ("trouser", "pants"),
        ("jean", "pants"),
        ("legging", "pants"),
        ("short", "shorts"),
        ("coat", "trench_coat"),
        ("jacket", "jacket"),
        ("blazer", "blazer"),
        ("shoe", "shoes"),
        ("sandal", "sandals"),
        ("boot", "boots"),
        ("bag", "bag"),
        ("watch", "watch"),
        ("necklace", "necklace"),
        ("earring", "earrings"),
        ("bracelet", "bracelet"),
        ("scarf", "scarf"),
        ("top", "shirt"),
        ("tshirt", "shirt"),
        ("tee", "shirt"),
        ("blouse", "shirt"),
        ("shirt", "shirt"),
    ]

    for keyword, category in keyword_map:
        if keyword in n:
            return category
    return "shirt"


def collect_files(upload_dirs):
    seen = set()
    files = []
    for upload_dir in upload_dirs:
        if not os.path.isdir(upload_dir):
            continue
        for name in os.listdir(upload_dir):
            if name.startswith("."):
                continue
            path = os.path.join(upload_dir, name)
            if not os.path.isfile(path):
                continue
            if name not in seen:
                seen.add(name)
                files.append(path)
    return files


def main():
    parser = argparse.ArgumentParser(description="Prepare evaluation dataset from uploaded images.")
    parser.add_argument("--out-dir", required=True, help="Destination image folder")
    parser.add_argument("--labels-csv", required=True, help="Output labels CSV")
    parser.add_argument(
        "--uploads",
        nargs="+",
        default=["backend/static/uploads", "static/uploads"],
        help="Upload directories to search",
    )
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    files = collect_files(args.uploads)
    with open(args.labels_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "true_category", "true_color_hex"])

        copied = 0
        for src in files:
            name = os.path.basename(src)
            dest_name = f"up_{copied:03d}_{name}"
            dest_path = os.path.join(args.out_dir, dest_name)
            shutil.copyfile(src, dest_path)

            suggested = suggest_category(name)
            writer.writerow([dest_name, suggested, ""])
            copied += 1

    print(f"Copied {copied} images to {args.out_dir}")
    print(f"Labels saved to {args.labels_csv} (suggested labels - edit if needed)")


if __name__ == "__main__":
    main()
