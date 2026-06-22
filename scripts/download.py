from datasets import load_dataset
import os

OUT_DIR = "data/raw/codexglue_defect_detection"
os.makedirs(OUT_DIR, exist_ok=True)

ds = load_dataset("google/code_x_glue_cc_defect_detection")

for split in ds.keys():
    out_path = os.path.join(OUT_DIR, f"{split}.jsonl")
    ds[split].to_json(out_path, orient="records", lines=True)
    print(f"Saved {split} to {out_path} | rows={len(ds[split])}")