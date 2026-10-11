"""Score explicitly annotated gold55 main-clause roles (in-sample only).

Fixture was losslessly derived from the user-approved gold55 JSON.
Omitted role != empty role. Variants must match as a whole.
"""
import base64
import json
import re
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent

def load_gold():
    data = (HERE / "data/gold55_approved_roles.zlib.b64").read_text().strip()
    return json.loads(zlib.decompress(base64.b64decode(data)).decode("utf-8"))

def normalize(x):
    return re.sub(r"\s+", " ", x).strip().lower()

def texts(values):
    return sorted(normalize(x) for x in values)

def score(predictions):
    gold = load_gold()
    if len(gold) != 55 or len(predictions) != 55:
        raise ValueError("Expected 55 approved cases and 55 actual predictions")
    results = []
    for cid, variants in gold.items():
        if cid not in predictions:
            raise ValueError("Missing prediction " + cid)
        comparisons = []
        for variant in variants:
            differences = {
                role: {"expected": texts(expected),
                       "actual": texts(predictions[cid].get(role, []))}
                for role, expected in variant.items()
                if texts(expected) != texts(predictions[cid].get(role, []))
            }
            comparisons.append(differences)
        best = min(comparisons, key=len)
        results.append({"id": cid, "passed": not best, "differences": best})
    return {"total": 55, "passed": sum(x["passed"] for x in results),
            "failed": [x for x in results if not x["passed"]],
            "scope": "annotated main-clause roles only",
            "in_sample": True}

if __name__ == "__main__":
    import sys
    predictions = json.loads(Path(sys.argv[1]).read_text())["predictions"]
    report = score(predictions)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["failed"]:
        raise SystemExit(1)
