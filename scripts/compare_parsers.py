"""Standalone comparison: dependency-root and subject proxies, not full SVOC accuracy."""
import csv, json, os, resource, statistics, time
from pathlib import Path
import spacy
import stanza

DATA=json.loads(Path(__file__).with_name("parser_cases.json").read_text())
def rss(): return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
def score(root,subject,expected):
    # Subject is a lexical head; gold labels are diagnostic proxies, not full parses.
    return int(root.lower()==expected["root"].lower()), int(subject.lower()==expected["subject"].lower())
def spacy_run(nlp,s):
    d=nlp(s); root=next((t for t in d if t.dep_=="ROOT"),None)
    if root is None:return "",""
    subj=next((t for t in d if t.dep_ in ("nsubj","nsubjpass","csubj","expl") and t.head==root),None)
    return root.text, subj.text if subj else ""
def stanza_run(nlp,s):
    d=nlp(s); ws=d.sentences[0].words
    root=next((w for w in ws if w.head==0),None)
    if root is None:return "",""
    subj=next((w for w in ws if w.head==root.id and w.deprel.startswith(("nsubj","csubj","expl"))),None)
    return root.text,subj.text if subj else ""
def benchmark(name,setup,run):
    t=time.perf_counter(); model=setup(); load=time.perf_counter()-t
    warm=run(model,DATA[0]["text"])
    start=time.perf_counter(); rows=[]
    for c in DATA:
        a=time.perf_counter(); root,subj=run(model,c["text"]); duration=time.perf_counter()-a
        r,s=score(root,subj,c)
        rows.append(dict(parser=name,text=c["text"],expected_root=c["root"],actual_root=root,root_ok=r,expected_subject=c["subject"],actual_subject=subj,subject_ok=s,seconds=round(duration,5)))
    return rows,dict(parser=name,load_seconds=round(load,3),total_seconds=round(time.perf_counter()-start,3),mean_seconds=round(statistics.mean(x["seconds"] for x in rows),4),root_accuracy=round(sum(x["root_ok"] for x in rows)/len(rows),3),subject_accuracy=round(sum(x["subject_ok"] for x in rows)/len(rows),3),max_rss_mb=round(rss(),1))
def main():
    results=[];summaries=[]
    for name,setup,run in [
        ("spaCy",lambda:spacy.load("en_core_web_sm",disable=["ner"]),spacy_run),
        ("Stanza",lambda:stanza.Pipeline("en",processors="tokenize,pos,lemma,depparse",use_gpu=False,verbose=False,download_method=None),stanza_run)]:
        rows,summary=benchmark(name,setup,run);results+=rows;summaries.append(summary)
        print(json.dumps(summary,ensure_ascii=False),flush=True)
    out=Path("parser-benchmark-results");out.mkdir(exist_ok=True)
    with (out/"cases.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=results[0].keys());w.writeheader();w.writerows(results)
    (out/"summary.json").write_text(json.dumps(summaries,indent=2))
    print("Benchmark complete; results in parser-benchmark-results",flush=True)
if __name__=="__main__":main()
