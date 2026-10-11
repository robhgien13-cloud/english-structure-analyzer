"""Score approved gold S/V/O/C/M fields only.

This tool requires both an approved gold file and an actual prediction report.
Missing gold roles are NOT treated as expected empty roles. Whole variants are
scored independently; the best complete variant may match.
"""
import argparse
import json
import re
from pathlib import Path

ROLES = "SVOCM"

def normalize(value):
    return re.sub(r"\s+", " ", value).strip().lower()

def role_texts(entries):
    return sorted(normalize(x["text"] if isinstance(x, dict) else x)
                  for x in entries)

def score(gold, report):
    cases = gold["cases"]
    predictions = report.get("predictions", {})
    if len(cases) != 55 or len(predictions) != 55:
        raise ValueError("Expected 55 gold cases and 55 actual predictions")
    details = []
    for case in cases:
        cid = case["id"]
        actual = predictions.get(cid)
        if actual is None:
            raise ValueError("Missing prediction: " + cid)
        variants = case.get("variants", [])
        results = []
        for variant in variants:
            main = next((c for c in variant["clauses"] if c.get("id") == "main"), None)
            if main is None:
                continue
            annotated = main.get("role_spans", {})
            if not annotated:
                continue
            differences = {}
            for role, expected in annotated.items():
                if role not in ROLES:
                    continue
                observed = actual.get(role, [])
                if role_texts(expected) != role_texts(observed):
                    differences[role] = {"expected": role_texts(expected),
                                         "actual": role_texts(observed)}
            results.append({"variant": variant.get("id"), "differences": differences,
                            "annotated_roles": list(annotated)})
        if not results:
            raise ValueError("No scored gold variant: " + cid)
        winner = min(results, key=lambda x: len(x["differences"]))
        details.append({"id": cid, "pass": not winner["differences"], **winner})
    return {"total": len(details), "passed": sum(x["pass"] for x in details),
            "failed": [x for x in details if not x["pass"]],
            "scope": "explicitly annotated main-clause roles only",
            "in_sample": True}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--actual", required=True)
    parser.add_argument("--output", default="gold55-accuracy-report.json")
    args = parser.parse_args()
    gold = json.loads(Path(args.gold).read_text(encoding="utf-8"))
    actual = json.loads(Path(args.actual).read_text(encoding="utf-8"))
    result = score(gold, actual)
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="failed"}, ensure_ascii=False))
    if result["failed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
