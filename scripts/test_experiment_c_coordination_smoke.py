"""Read-only smoke checks for coordination and negative/unsupported patterns."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analyzer import EnglishStructureAnalyzer
app=EnglishStructureAnalyzer()
cases=[
 ("positive_predicate","She opened the door and entered the room.","predicate",1),
 ("positive_complement","He is smart but sometimes careless.","complement",1),
 ("negative_noun","She bought apples and oranges.",None,0),
 ("negative_independent","She opened the door, and he entered the room.",None,0),
 ("negative_adj_nominal","The smart and careful student smiled.",None,0),
 ("negative_two_sentences","She smiled. He waved.",None,0),
 ("negative_object_complement","I found the book useful.",None,0),
]
rows=[]
for label,source,kind,count in cases:
    parsed=app.analyze(source)
    groups=[g for sentence in parsed["sentences"] for g in sentence.get("coordination_groups",[])]
    passed=len(groups)==count and (not groups or groups[0].get("kind")==kind)
    rows.append({"id":label,"text":source,"expected_count":count,"observed":groups,"passed":passed})
out=ROOT/"parser-40-results/experiment-c-coordination-smoke.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({"cases":rows,"passed":sum(x["passed"] for x in rows),"total":len(rows)},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"passed":sum(x["passed"] for x in rows),"total":len(rows)}))
if not all(x["passed"] for x in rows):
    raise SystemExit(1)
