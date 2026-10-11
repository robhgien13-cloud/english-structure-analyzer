"""Read-only spaCy and normalized analyzer trace for six mismatching cases."""
import json
import sys
from pathlib import Path
import spacy

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analyzer import EnglishStructureAnalyzer

IDS={"G019","G028","G029","G031","G034","G040"}
cases=json.loads((ROOT/"tests/data/parser_gold_40_candidate_v1.json").read_text(encoding="utf-8"))["cases"]
nlp=spacy.load("en_core_web_sm",disable=["ner"])
app=EnglishStructureAnalyzer()
rows=[]
for case in cases:
    if case["id"] not in IDS:
        continue
    doc=nlp(case["text"])
    normalized=app._convert_sentence(next(doc.sents))
    analysis=app.analyze(case["text"])["sentences"][0]
    main=next((c for c in analysis.get("clauses",[]) if c.get("type")=="main"),None)
    rows.append({
        "id":case["id"],"text":case["text"],"candidate_main":case["main"],
        "candidate_audit":case.get("audit",{}),
        "raw_tokens":[{"i":t.i+1,"text":t.text,"pos":t.pos_,"tag":t.tag_,"dep":t.dep_,"head":t.head.i+1 if t.head!=t else 0} for t in doc],
        "normalized_tokens":[{"i":w.id,"text":w.text,"pos":w.upos,"tag":w.xpos,"dep":w.deprel,"head":w.head} for w in normalized.words],
        "main_core":main.get("core") if main else None,
        "all_clauses":analysis.get("clauses",[]),
        "relations":analysis.get("relations",[]),
        "syntax_validation":analysis.get("syntax_validation"),
        "warnings":analysis.get("warnings",[]),
    })
out=ROOT/"parser-40-results"/"experiment-c-six-case-trace.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps({"kind":"read_only_actual_model_trace","cases":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"traced_ids":[r["id"] for r in rows],"path":str(out)},ensure_ascii=False))
