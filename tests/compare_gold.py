"""Compare the current analyzer against the 40 approved gold cases.

Run from repository root: python tests/compare_gold.py
Requires: spacy and python -m spacy download en_core_web_sm
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analyzer import EnglishStructureAnalyzer

GOLD = Path(__file__).parent / "gold" / "english_structure_gold_G001-G040.json"
ROLES = ("S", "V", "O", "C", "M")


def values(core, role):
    return [str(item.get("text", "")).strip() for item in core.get(role, [])]


def main_clause(result):
    sentences = result.get("sentences", [])
    if not sentences:
        return None
    return next((c for c in sentences[0].get("clauses", []) if c.get("type") == "main"), None)


def compare():
    gold = json.loads(GOLD.read_text(encoding="utf-8"))["cases"]
    analyzer = EnglishStructureAnalyzer()
    total = matched = 0
    for case in gold:
        try:
            result = analyzer.analyze(case["sentence"])
            main = main_clause(result)
            if main is None:
                print(f'{case["id"]}: NO MAIN CLAUSE')
                total += len(ROLES)
                continue
            for role in ROLES:
                expected = case["main_clause"].get(role, [])
                actual = values(main["core"], role)
                total += 1
                if expected == actual:
                    matched += 1
                else:
                    print(f'{case["id"]} {role}: expected={expected!r}; actual={actual!r}')
        except Exception as exc:
            total += len(ROLES)
            print(f'{case["id"]}: ERROR {type(exc).__name__}: {exc}')
    print(f"Main-clause exact role matches: {matched}/{total}")
    print("Note: This is a diagnostic comparison, not a complete validation of")
    print("subordinate clauses, phrase spans, or token offsets.")
    return 0 if matched == total else 1


if __name__ == "__main__":
    try:
        sys.exit(compare())
    except OSError as exc:
        print(f"Cannot initialize spaCy model: {exc}", file=sys.stderr)
        sys.exit(2)
