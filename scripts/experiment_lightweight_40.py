"""Lightweight local parser experiment: compare spaCy pipeline configurations.
This is a resource baseline, NOT a validated replacement for SuPar/benepar.
Run: python scripts/experiment_lightweight_40.py
Separate process per mode for fair peak RSS: --mode full / parser-only.
"""
import argparse
import json
import resource
import time
from pathlib import Path
import spacy

p = argparse.ArgumentParser()
p.add_argument("--mode", choices=["full", "parser-only"], required=True)
args = p.parse_args()
root = Path(__file__).resolve().parents[1]
cases = json.loads((root / "tests/data/parser_gold_40.json").read_text())["cases"]
# Parser-only keeps tok2vec and parser; POS-dependent diagnostic logic will
# require a separate POS solution, so this is not yet a deployable candidate.
disable = ["ner"] if args.mode == "full" else [
    "ner", "tagger", "attribute_ruler", "lemmatizer"
]
start = time.perf_counter()
nlp = spacy.load("en_core_web_sm", disable=disable)
load_s = time.perf_counter() - start
results = []
start = time.perf_counter()
for case in cases:
    doc = nlp(case["text"])
    results.append({
        "id": case["id"],
        "root": [t.text for t in doc if t.dep_ == "ROOT"],
        "dependencies": [{"text": t.text, "dep": t.dep_,
                          "head": t.head.i, "pos": t.pos_} for t in doc]
    })
elapsed = time.perf_counter() - start
peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
report = {
    "mode": args.mode, "sentences": len(results), "load_seconds": round(load_s, 3),
    "parse_seconds": round(elapsed, 3), "peak_rss_mb": round(peak_mb, 1),
    "components": nlp.pipe_names, "results": results,
    "warning": "No SVOC scoring; parser-only lacks POS/lemmas used by analyzer.py."
}
out = root / "parser-40-results"
out.mkdir(exist_ok=True)
(out / ("lightweight-" + args.mode + ".json")).write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k:v for k,v in report.items() if k!="results"},ensure_ascii=False))
