import argparse
import csv
import os
import shutil
import sqlite3


def resolve_upload_path(upload_dirs, filename):
    candidates = [f"uploaded_{filename}", filename]
    for upload_dir in upload_dirs:
        for cand in candidates:
            path = os.path.join(upload_dir, cand)
            if os.path.exists(path):
                return path
    return None


def main():
    parser = argparse.ArgumentParser(description="Prepare evaluation dataset from stylesync.db garments table.")
    parser.add_argument("--db", default="backend/stylesync.db", help="Path to SQLite DB")
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

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    cur.execute("SELECT id, filename, color, category FROM garments")
    rows = cur.fetchall()
    conn.close()

    with open(args.labels_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "true_category", "true_color_hex"])

        copied = 0
        for garment_id, filename, color, category in rows:
            if not filename or not category:
                continue
            src = resolve_upload_path(args.uploads, filename)
            if not src:
                print(f"[SKIP] Missing file for {filename}")
                continue

            dest_name = f"db_{garment_id}_{filename}"
            dest_path = os.path.join(args.out_dir, dest_name)
            shutil.copyfile(src, dest_path)
            writer.writerow([dest_name, category, color or ""])
            copied += 1

    print(f"Copied {copied} images to {args.out_dir}")
    print(f"Labels saved to {args.labels_csv}")


if __name__ == "__main__":
    main()
