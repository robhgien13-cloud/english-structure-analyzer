"""Read-only, provisional comparison of main roles and full adjective complements.

Consumes real app trace and the existing candidate gold. Never rewrites either.
Coordination is explicitly unscored.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "tests/data/parser_gold_40_candidate_v1.json"
TRACE = ROOT / "parser-40-results/experiment-c-six-case-trace.json"
BASE = ROOT / "parser-40-results/candidate_comparison.json"
OUT = ROOT / "parser-40-results/candidate_extended_comparison.json"

def norm(text):
    return " ".join(text.casefold().split())

def main():
    gold = {c["id"]: c for c in json.loads(GOLD.read_text(encoding="utf-8"))["cases"]}
    base = json.loads(BASE.read_text(encoding="utf-8"))
    traces = {c["id"]: c for c in json.loads(TRACE.read_text(encoding="utf-8"))["cases"]}
    details = []
    for row in base["rows"]:
        cid = row["id"]
        candidate = gold[cid]
        complement = candidate.get("audit", {}).get("complement")
        if not complement:
            continue
        trace = traces.get(cid)
        core = (trace or {}).get("main_core") or {}
        actual_c = core.get("C", [])
        heads = [c.get("text") for c in actual_c if isinstance(c, dict)]
        fulls = [c.get("full_text") for c in actual_c if isinstance(c, dict)]
        expected_core = complement.get("core")
        expected_full = complement.get("full")
        head_match = any(isinstance(x, str) and norm(x) == norm(expected_core) for x in heads)
        full_match = any(isinstance(x, str) and norm(x) == norm(expected_full) for x in fulls)
        details.append({"id": cid, "expected_core": expected_core, "observed_core": heads,
                        "core_status": "match" if head_match else "mismatch",
                        "expected_full": expected_full, "observed_full": fulls,
                        "full_status": "match" if full_match else "mismatch",
                        "status": "match" if head_match and full_match else "mismatch"})
    raw = base["role_totals"]
    # Extended matching does not replace the raw role comparison.
    report = {"status": "provisional_unapproved_candidate",
              "original_role_totals": raw,
              "extended_complement_checks": details,
              "extended_complement_match": sum(x["status"] == "match" for x in details),
              "extended_complement_total": len(details),
              "coordination": {"G038": "not_evaluated", "G039": "not_evaluated"},
              "warning": "Do not present role-string agreement as grammatical accuracy. "
                         "Coordination, clauses and modifiers are not fully scored."}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"original": raw, "extended_complement_match": report["extended_complement_match"],
                      "extended_complement_total": len(details),
                      "coordination": "not_evaluated"}, ensure_ascii=False))

if __name__ == "__main__":
    main()
