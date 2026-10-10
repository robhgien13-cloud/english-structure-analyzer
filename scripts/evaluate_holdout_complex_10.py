"""Run blind holdout probes without scoring against invented gold."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analyzer import EnglishStructureAnalyzer

cases = json.loads((ROOT / "tests/data/holdout_complex_10.json").read_text(encoding="utf-8"))["cases"]
app = EnglishStructureAnalyzer()
rows = []
for case in cases:
    result = app.analyze(case["text"])
    sentence = result["sentences"][0]
    main = next((c for c in sentence["clauses"] if c["type"] == "main"), None)
    core = main["core"] if main else {k: [] for k in "SVOCM"}
    actual = {k: [e["text"] for e in core.get(k, [])] for k in "SVOCM"}
    rows.append({"id": case["id"], "text": case["text"], "main": actual,
                 "warnings": sentence["warnings"],
                 "tags": sentence["tags"],
                 "clauses": [{"type": c["type"], "core": {
                     k: [e["text"] for e in c["core"][k]] for k in "SVOCM"
                 }} for c in sentence["clauses"]]})
    print("BLIND HOLDOUT", case["id"], json.dumps(actual, ensure_ascii=False))
out = ROOT / "parser-40-results"
out.mkdir(exist_ok=True)
(out / "holdout-complex-10.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print("BLIND HOLDOUT COMPLETE: 10 cases, no accuracy score assigned.")
