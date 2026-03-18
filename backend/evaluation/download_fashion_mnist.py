import argparse
import csv
import gzip
import os
import random
import struct
import urllib.request
from typing import List, Tuple

import numpy as np
from PIL import Image

BASE_URL = "http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/"
FILES = {
    "images": "t10k-images-idx3-ubyte.gz",
    "labels": "t10k-labels-idx1-ubyte.gz",
}

LABEL_MAP = {
    0: "shirt",        # T-shirt/top
    1: "pants",        # Trouser
    2: "cardigan",     # Pullover
    3: "dress",
    4: "trench_coat",  # Coat
    5: "sandals",      # Sandal
    6: "shirt",
    7: "shoes",        # Sneaker
    8: "bag",
    9: "boots",        # Ankle boot
}


def download_file(url: str, dest: str) -> None:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest):
        return
    print(f"Downloading {url}")
    urllib.request.urlretrieve(url, dest)


def read_images(path: str) -> np.ndarray:
    with gzip.open(path, "rb") as f:
        magic, num, rows, cols = struct.unpack(">IIII", f.read(16)
        )
        if magic != 2051:
            raise ValueError("Invalid image file magic number")
        data = f.read(num * rows * cols)
        images = np.frombuffer(data, dtype=np.uint8).reshape(num, rows, cols)
        return images


def read_labels(path: str) -> List[int]:
    with gzip.open(path, "rb") as f:
        magic, num = struct.unpack(">II", f.read(8))
        if magic != 2049:
            raise ValueError("Invalid label file magic number")
        data = f.read(num)
        labels = np.frombuffer(data, dtype=np.uint8).tolist()
        return labels


def save_sample(images: np.ndarray, labels: List[int], out_dir: str, csv_path: str, sample_size: int) -> None:
    os.makedirs(out_dir, exist_ok=True)

    indices = list(range(len(labels)))
    random.seed(42)
    random.shuffle(indices)
    indices = indices[:sample_size]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "true_category", "true_color_hex"])

        for idx in indices:
            label = labels[idx]
            category = LABEL_MAP.get(label, "shirt")
            img = Image.fromarray(images[idx])
            filename = f"fm_{idx:05d}_{category}.png"
            img.save(os.path.join(out_dir, filename))
            writer.writerow([filename, category, ""])


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and sample Fashion-MNIST for evaluation.")
    parser.add_argument("--out-dir", required=True, help="Output image directory")
    parser.add_argument("--labels-csv", required=True, help="Output labels CSV")
    parser.add_argument("--sample-size", type=int, default=50, help="Number of images to sample")
    parser.add_argument("--cache-dir", default="backend/evaluation/fashion_mnist", help="Download cache directory")
    args = parser.parse_args()

    images_path = os.path.join(args.cache_dir, FILES["images"])
    labels_path = os.path.join(args.cache_dir, FILES["labels"])

    download_file(BASE_URL + FILES["images"], images_path)
    download_file(BASE_URL + FILES["labels"], labels_path)

    images = read_images(images_path)
    labels = read_labels(labels_path)

    if len(images) != len(labels):
        raise ValueError("Image/label count mismatch")

    save_sample(images, labels, args.out_dir, args.labels_csv, args.sample_size)
    print(f"Saved {args.sample_size} images to {args.out_dir}")
    print(f"Saved labels to {args.labels_csv}")


if __name__ == "__main__":
    main()
