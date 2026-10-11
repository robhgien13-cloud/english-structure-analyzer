"""Exercise the experimental rubric adapter against the real spaCy model.

This is an execution/shape regression, NOT gold-label accuracy scoring.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
from analyzer import EnglishStructureAnalyzer
from gold55_school_grammar_adapter import adapt_main_clause

cases = json.loads((ROOT / "tests/data/gold55_sentences.json").read_text(encoding="utf-8"))["cases"]
assert len(cases) == 55
analyzer = EnglishStructureAnalyzer()
errors = []
predictions = {}
for case in cases:
    try:
        output = analyzer.analyze(case["sentence"])
        roles = adapt_main_clause(output)
        if set(roles) != set("SVOCM"):
            raise ValueError("Missing roles")
        if not all(isinstance(roles[r], list) for r in "SVOCM"):
            raise ValueError("Role is not a list")
        predictions[case["id"]] = {r: [item.get("text", "") for item in roles[r]] for r in "SVOCM"}
        print(f'{case["id"]}: adapter ran')
    except Exception as e:
        errors.append({"id": case["id"], "error": str(e)})
report = {"total":len(cases),"executed":len(predictions),"errors":errors,
          "predictions":predictions,"gold_accuracy":"NOT MEASURED"}
(ROOT / "gold55-adapter-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report,ensure_ascii=False))
if errors:
    raise SystemExit(1)
