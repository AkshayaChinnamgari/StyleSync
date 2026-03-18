import argparse
import csv
import os
from PIL import Image

CATEGORIES = [
    "shirt",
    "pants",
    "dress",
    "kurta",
    "skirt",
    "shorts",
    "cardigan",
    "jacket",
    "blazer",
    "trench_coat",
    "shoes",
    "sandals",
    "boots",
    "bag",
    "necklace",
    "bracelet",
    "earrings",
    "watch",
    "scarf",
    "hat",
    "gloves",
    "belt",
]


def main():
    parser = argparse.ArgumentParser(description="Manual labeling for evaluation images.")
    parser.add_argument("--images-dir", required=True, help="Folder with images to label")
    parser.add_argument("--labels-csv", required=True, help="Output labels CSV")
    args = parser.parse_args()

    files = [f for f in os.listdir(args.images_dir) if not f.startswith(".")]
    files.sort()

    with open(args.labels_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "true_category", "true_color_hex"])

        for idx, name in enumerate(files, start=1):
            path = os.path.join(args.images_dir, name)
            if not os.path.isfile(path):
                continue

            print(f"\n[{idx}/{len(files)}] {name}")
            print("Categories:")
            for i, cat in enumerate(CATEGORIES, start=1):
                print(f"  {i:02d}. {cat}")

            try:
                Image.open(path).show()
            except Exception as e:
                print(f"Could not open image: {e}")

            choice = input("Enter category (name or number), or 'skip': ").strip().lower()
            if choice == "skip" or choice == "":
                print("Skipped")
                continue

            if choice.isdigit():
                num = int(choice)
                if 1 <= num <= len(CATEGORIES):
                    category = CATEGORIES[num - 1]
                else:
                    print("Invalid number, skipped")
                    continue
            else:
                if choice not in CATEGORIES:
                    print("Invalid category, skipped")
                    continue
                category = choice

            writer.writerow([name, category, ""])
            print(f"Saved: {name} -> {category}")

    print(f"\nLabels saved to {args.labels_csv}")


if __name__ == "__main__":
    main()
