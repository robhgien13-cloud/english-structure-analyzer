"""Smoke-test the real spaCy-backed analyzer on 55 approved English sentences.

Run after the sentence fixture is committed to tests/data/gold55_sentences.json.
This tests execution and output shape, NOT gold-label accuracy.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analyzer import EnglishStructureAnalyzer
from gold55_school_grammar_adapter import adapt_main_clause

GOLD = ROOT / "tests" / "data" / "gold55_sentences.json"

def main():
    if not GOLD.exists():
        raise SystemExit("MISSING GOLD: tests/data/gold55_unified.json must be added before smoke test")
    cases = json.loads(GOLD.read_text(encoding="utf-8"))["cases"]
    assert len(cases) == 55
    analyzer = EnglishStructureAnalyzer()
    failures = []
    for case in cases:
        try:
            result = analyzer.analyze(case["sentence"])
            if not isinstance(result, dict) or not result:
                raise ValueError("Empty or non-object analyzer output")
            roles = adapt_main_clause(result)
            if set(roles) != set("SVOCM") or not all(isinstance(roles[r], list) for r in "SVOCM"):
                raise ValueError("Adapter returned invalid S/V/O/C/M shape")
            print(f'{case["id"]}: parsed and adapted')
        except Exception as exc:
            failures.append({"id": case["id"], "error": str(exc)})
            print(f'{case["id"]}: ERROR {exc}')
    report = {"total": len(cases), "executed": len(cases) - len(failures),
              "errors": failures, "gold_accuracy": "NOT MEASURED"}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
