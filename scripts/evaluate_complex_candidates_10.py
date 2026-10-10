"""Diagnostic evaluation of 10 unseen complex syntax candidates (not validated accuracy)."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analyzer import EnglishStructureAnalyzer

cases = json.loads((ROOT / "tests/data/complex_candidates_10.json").read_text(encoding="utf-8"))["cases"]
app = EnglishStructureAnalyzer()
rows = []
for case in cases:
    result = app.analyze(case["text"])
    sentence = result["sentences"][0]
    main = next((c for c in sentence["clauses"] if c["type"] == "main"), None)
    core = main["core"] if main else {k: [] for k in "SVOCM"}
    actual = {k: [e["text"] for e in core.get(k, [])] for k in "SVOCM"}
    v_tokens = [sentence["tokens"][i-1]["text"] for i in sorted(
        {t for e in core.get("V", []) for t in e["token_ids"]})]
    if case["id"] in {"T061", "T062", "T063", "T064", "T065", "T066", "T067", "T068", "T069", "T070"}:
        print("RAW", case["id"], [(t.text, t.dep_, t.head.text) for t in app.nlp(case["text"])])
        print("NORMALIZED", case["id"], [(t["text"], t["deprel"], t["head"]) for t in sentence["tokens"]])
    expected = case["expected"]
    match = {
        "S": actual["S"] == [expected["S"]],
        "V_tokens": [t.lower() for t in v_tokens] == [t.lower() for t in expected["V_tokens"]],
        "O": actual["O"] == expected["O"],
        "C": actual["C"] == expected["C"],
        "M": sorted(actual["M"]) == sorted(expected["M"]),
    }
    rows.append({
        "id": case["id"], "category": case["category"], "text": case["text"],
        "expected": expected, "actual": actual, "actual_V_tokens": v_tokens,
        "match": match, "tags": sentence["tags"], "warnings": sentence["warnings"],
        "clauses": [{"type": c["type"], "core": {
            k: [e["text"] for e in c["core"][k]] for k in "SVOCM"
        }} for c in sentence["clauses"]],
    })
    print(case["id"], case["category"], "matches:", match, "actual:", actual)
out = ROOT / "parser-40-results"
out.mkdir(exist_ok=True)
(out / "complex-candidates-10.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
summary = {k: sum(r["match"][k] for r in rows) for k in ("S", "V_tokens", "O", "C", "M")}
print("DRAFT MATCH COUNTS (NOT VERIFIED ACCURACY):", json.dumps(summary))
print("MISMATCH IDS:", {k: [r["id"] for r in rows if not r["match"][k]] for k in summary})
