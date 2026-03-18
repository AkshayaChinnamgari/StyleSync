# Evaluation (StyleSync)

## 1) Prepare a small labeled set

- Place 50–100 garment images in a folder (e.g., `backend/evaluation/images`).
- Create a CSV using `labels_template.csv` with columns:
  - `filename` (image filename)
  - `true_category` (ground truth label)
  - `true_color_hex` (optional, e.g., `#3366cc`)

## 2) Run evaluation

From the repo root, run:

```
python backend/evaluation/evaluate_metrics.py \
  --images-dir backend/evaluation/images \
  --labels backend/evaluation/labels.csv \
  --out backend/evaluation/metrics.json
```

## 3) Results

The script prints a summary and saves JSON metrics to the `--out` file.

### Metrics included

- Classification accuracy
- Precision/Recall/F1 (macro + weighted)
- Color HEX exact match rate
- Mean RGB distance and mean ΔE (Lab) when `true_color_hex` is provided
