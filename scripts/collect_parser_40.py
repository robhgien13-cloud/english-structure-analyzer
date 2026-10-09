"""Collect raw parses for 40 candidate cases; NO automatic accuracy claims."""
import argparse
import json
import re
import time
import traceback
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--engine", choices=["spacy", "supar", "benepar"], required=True)
args = p.parse_args()
root = Path(__file__).resolve().parents[1]
cases = json.loads((root/"tests/data/parser_gold_40.json").read_text(encoding="utf-8"))["cases"]
out = root/"parser-40-results"
out.mkdir(exist_ok=True)
report = {"engine":args.engine,"gold_status":"pending_human_review","results":[],"status":"started"}

def memory():
    values = {}
    with open("/proc/self/status", encoding="utf-8") as f:
        for line in f:
            if line.startswith(("VmRSS:","VmHWM:")):
                k,v = line.split(":",1)
                values[k+"_mb"] = round(int(v.strip().split()[0])/1024,1)
    return values

def tokens(s):
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|[^\w\s]", s)

try:
    report["before_load"]=memory()
    if args.engine=="spacy":
        import spacy
        model=spacy.load("en_core_web_sm")
    elif args.engine=="supar":
        import torch
        torch.set_num_threads(1)
        from supar import Parser
        model=Parser.load("crf-con-en")
    else:
        import spacy
        import benepar
        model=spacy.blank("en")
        model.add_pipe("benepar",config={"model":"benepar_en3"})
    report["after_load"]=memory()
    for case in cases:
        t=time.perf_counter()
        entry={"id":case["id"],"text":case["text"]}
        try:
            if args.engine=="spacy":
                doc=model(case["text"])
                entry["tokens"]=[{"text":x.text,"start":x.idx,"end":x.idx+len(x.text),"dep":x.dep_,"head":x.head.i,"pos":x.pos_} for x in doc]
            elif args.engine=="supar":
                doc=model.predict([tokens(case["text"])],verbose=False)
                entry["tree"]=str(doc.trees[0])
            else:
                doc=model(case["text"])
                entry["tree"]=list(doc.sents)[0]._.parse_string
            entry["status"]="success"
        except Exception:
            entry["status"]="failed"
            entry["error"]=traceback.format_exc()
        entry["seconds"]=round(time.perf_counter()-t,4)
        report["results"].append(entry)
    report["status"]="success" if all(x["status"]=="success" for x in report["results"]) else "partial"
except Exception:
    report["status"]="failed"
    report["error"]=traceback.format_exc()
finally:
    report["after_run"]=memory()
    (out/(args.engine+".json")).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"engine":args.engine,"status":report["status"],"completed":len(report["results"]),"memory":report["after_run"]},ensure_ascii=False))
if report["status"]=="failed":
    raise SystemExit(1)
