"""Read-only real-model trace of coordination cases G038 and G039."""
import json
import sys
from pathlib import Path
import spacy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analyzer import EnglishStructureAnalyzer
gold=json.loads((ROOT/"tests/data/parser_gold_40_candidate_v1.json").read_text(encoding="utf-8"))
app=EnglishStructureAnalyzer()
nlp=spacy.load("en_core_web_sm",disable=["ner"])
rows=[]
for case in gold["cases"]:
    if case["id"] not in {"G038","G039"}:
        continue
    doc=nlp(case["text"])
    analysis=app.analyze(case["text"])["sentences"][0]
    rows.append({
        "id":case["id"],"text":case["text"],
        "candidate_coordination":case.get("audit",{}).get("coordination"),
        "raw_tokens":[{"text":t.text,"dep":t.dep_,"head":t.head.text,"pos":t.pos_} for t in doc],
        "clauses":analysis["clauses"],"relations":analysis["relations"],
        "tags":analysis["tags"],"warnings":analysis["warnings"]
    })
out=ROOT/"parser-40-results/experiment-c-coordination-trace.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({"status":"read_only_actual_model_trace","cases":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"cases":len(rows),"ids":[x["id"] for x in rows],"output":str(out)},ensure_ascii=False))
