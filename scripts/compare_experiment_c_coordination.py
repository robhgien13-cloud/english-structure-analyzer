"""Read-only comparison of real coordination_groups to unapproved candidate."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analyzer import EnglishStructureAnalyzer
cases=json.loads((ROOT/"tests/data/parser_gold_40_candidate_v1.json").read_text(encoding="utf-8"))["cases"]
app=EnglishStructureAnalyzer()
results=[]
for case in cases:
    if case["id"] not in {"G038","G039"}: continue
    actual=app.analyze(case["text"])["sentences"][0].get("coordination_groups",[])
    expected=case["audit"]["coordination"]
    def normalize(obj):
        if isinstance(obj,str): return " ".join(obj.casefold().split())
        if isinstance(obj,list): return [normalize(x) for x in obj]
        if isinstance(obj,dict): return {k:normalize(v) for k,v in obj.items()}
        return obj
    def norm_members(members):
        result=[]
        for m in members:
            item={}
            for k,v in m.items():
                item[k]=normalize(v if isinstance(v,list) else [v])
            result.append(item)
        return result
    matches=[]
    for group in actual:
        match=(group["kind"]==expected["kind"] and
               group["conjunction"]==expected["conjunction"] and
               normalize(group["shared"])==normalize(expected["shared"]) and
               norm_members(group["members"])==norm_members(expected["members"]))
        matches.append(match)
    results.append({"id":case["id"],"status":"match" if any(matches) else "mismatch",
                    "expected":expected,"actual":actual})
out=ROOT/"parser-40-results/experiment-c-coordination-comparison.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({"status":"provisional_unapproved_candidate","rows":results,
                          "match":sum(r["status"]=="match" for r in results),
                          "total":len(results)},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"match":sum(r["status"]=="match" for r in results),"total":len(results)},ensure_ascii=False))
