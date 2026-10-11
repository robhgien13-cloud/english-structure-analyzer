"""Compare experiment-C parser output with unapproved 40-case candidate.

Run: python scripts/compare_gold_candidate_40.py --predictions PATH.json
Input must contain actual parser predictions, not synthetic values.
Supports {"results":[{"id":"G001","main":{"S":"She","V":"is","O":[],"C":"happy"}}]}
or a list with the same records. Unsupported/missing roles are NOT counted correct.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "tests/data/parser_gold_40_candidate_v1.json"
ROLES = ("S", "V", "O", "C")


def normalized(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip().casefold()]
    if isinstance(value, list):
        values = []
        for item in value:
            if isinstance(item, str):
                values.append(item.strip().casefold())
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                values.append(item["text"].strip().casefold())
            else:
                return None
        return sorted(values)
    if isinstance(value, dict) and isinstance(value.get("text"), str):
        return [value["text"].strip().casefold()]
    return None


def evaluate(gold, predictions):
    lookup = {r["id"]: r for r in predictions if isinstance(r, dict) and "id" in r}
    rows = []
    for case in gold["cases"]:
        actual = lookup.get(case["id"])
        main = actual.get("main") if isinstance(actual, dict) else None
        roles = {}
        for role in ROLES:
            expected = normalized(case["main"].get(role))
            if not isinstance(main, dict) or role not in main:
                roles[role] = {"status": "not_evaluated", "expected": expected}
                continue
            observed = normalized(main[role])
            roles[role] = {
                "status": "match" if observed is not None and observed == expected else
                          "unsupported_format" if observed is None else "mismatch",
                "expected": expected, "observed": observed,
            }
        coordination = case.get("audit", {}).get("coordination")
        rows.append({
            "id": case["id"], "text": case["text"], "roles": roles,
            "coordination_candidate": coordination,
            "coordination_status": "not_evaluated" if coordination else "not_applicable",
            "note": "Candidate gold is unapproved; matches are provisional, not accuracy claims.",
        })
    totals = {k: sum(v["status"] == k for row in rows for v in row["roles"].values())
              for k in ("match", "mismatch", "not_evaluated", "unsupported_format")}
    return {"status": "provisional_candidate_comparison", "gold_status": gold["status"],
            "cases": len(rows), "role_totals": totals, "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("parser-40-results/candidate_comparison.json"))
    args = parser.parse_args()
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    source = json.loads(args.predictions.read_text(encoding="utf-8"))
    predictions = source.get("results", []) if isinstance(source, dict) else source
    if not isinstance(predictions, list):
        raise ValueError("Predictions must be a list or an object with a results list.")
    report = evaluate(gold, predictions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cases": report["cases"], "role_totals": report["role_totals"],
                      "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
