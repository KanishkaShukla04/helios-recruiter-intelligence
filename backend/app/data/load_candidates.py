from pathlib import Path
import json

DATA_PATH = Path(__file__).parent / "candidates.jsonl"

print("Resolved path:", DATA_PATH.resolve())
print("Exists:", DATA_PATH.exists())


def load_candidates(limit=None):
    candidates = []

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            candidates.append(json.loads(line))

    return candidates