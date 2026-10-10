"""Independent 40-case spaCy baseline vs app normalization experiment.
Run after installing requirements and en_core_web_sm:
python scripts/experiment_spacy_40.py
Does not alter production or claim accuracy.
"""
import json
from pathlib import Path
import spacy
from analyzer import EnglishStructureAnalyzer

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "tests/data/parser_gold_40.json").read_text())["cases"]
nlp = spacy.load("en_core_web_sm", disable=["ner"])
app = EnglishStructureAnalyzer()
rows = []
for case in CASES:
    doc = nlp(case["text"])
    raw_roots = [t.text for t in doc if t.dep_ == "ROOT"]
    result = app.analyze(case["text"])["sentences"][0]
    main = next((c for c in result["clauses"] if c["type"] == "main"), None)
    core = main["core"] if main else {}
    get = lambda key: [e["text"] for e in core.get(key, [])]
    gold = case["main"]
    actual_s, actual_v = get("S"), get("V")
    rows.append({
        "id": case["id"], "text": case["text"],
        "raw_root": raw_roots, "normalized_root": result["root_token"],
        "gold_S": gold["S"], "pred_S": actual_s,
        "gold_V": gold["V"], "pred_V": actual_v,
        "S_exact": actual_s == [gold["S"]],
        "V_exact": actual_v == [gold["V"]],
        "gold_O": gold["O"], "pred_O": get("O"),
        "gold_C": gold["C"], "pred_C": get("C"),
        "warnings": result["warnings"],
    })
out = ROOT / "parser-40-results"
out.mkdir(exist_ok=True)
(out / "spacy-app-normalized.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "cases": len(rows),
    "S_exact": sum(x["S_exact"] for x in rows),
    "V_exact": sum(x["V_exact"] for x in rows),
    "note": "Exact diagnostic skeleton spans; not grammatical accuracy."
}, ensure_ascii=False))
