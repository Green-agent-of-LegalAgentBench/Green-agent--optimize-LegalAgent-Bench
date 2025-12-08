import json
from pathlib import Path

# =========================
#  ONLY change this folder name if needed
# This folder must contain your *.jsonl files
# =========================
INPUT_DIR = Path("database_resource-raw/hugging face copy")

# =========================
# Output file (merged clean dataset)
# =========================
OUTPUT_FILE = Path("disc_merged_clean.json")

all_data = []

print(" Scanning input directory...")

# =========================
# Read all .jsonl files
# =========================
for file in INPUT_DIR.glob("*.jsonl"):
    print(f"Reading file: {file.name}")

    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line.strip())
                all_data.append(item)
            except Exception as e:
                print(" JSON parse error:", e)

print(f" Total samples loaded: {len(all_data)}")

# =========================
#  Save merged clean JSON
# =========================
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

print(" Clean dataset successfully saved as:", OUTPUT_FILE)
