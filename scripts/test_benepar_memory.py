"""Measure benepar memory in isolated CPU processes, with and without cleanup."""
import argparse, ctypes, gc, json, os, resource, subprocess, sys, time, traceback
from pathlib import Path
OUT = Path("benepar-memory-results")
OUT.mkdir(exist_ok=True)
SENTENCES = ["The man who smiled left.", "When I arrived home, my mother was cooking dinner.", "The book that my teacher recommended yesterday was surprisingly difficult to understand."]

def memory():
    d = {}
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith(("VmRSS:", "VmHWM:")):
                k, v = line.split(":", 1)
                d[k + "_mb"] = round(int(v.strip().split()[0]) / 1024, 1)
    return d

def worker(mode):
    report = {"mode": mode, "status": "started", "measurements": []}
    def sample(stage):
        report["measurements"].append({"stage": stage, **memory()})
        (OUT / (mode + ".json")).write_text(json.dumps(report, indent=2))
    try:
        sample("start")
        import torch
        torch.set_num_threads(1)
        import spacy, benepar
        sample("imports")
        benepar.download("benepar_en3")
        sample("download")
        nlp = spacy.blank("en")
        nlp.add_pipe("sentencizer")
        nlp.add_pipe("benepar", config={"model": "benepar_en3"})
        sample("model_loaded")
        if mode == "cleanup":
            gc.collect()
            try:
                ctypes.CDLL("libc.so.6").malloc_trim(0)
            except Exception as e:
                report["trim_warning"] = str(e)
            sample("after_cleanup")
        with torch.inference_mode():
            for i, sentence in enumerate(SENTENCES):
                t = time.perf_counter()
                doc = nlp(sentence)
                report.setdefault("parses", []).append({"text": sentence, "parse": list(doc.sents)[0]._.parse_string, "seconds": round(time.perf_counter()-t, 3)})
                sample("parsed_" + str(i + 1))
        report["status"] = "success"
    except Exception:
        report["status"] = "failed"
        report["error"] = traceback.format_exc()
    finally:
        sample("finished")
        print(json.dumps(report, indent=2), flush=True)
    if report["status"] != "success":
        sys.exit(1)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        worker(sys.argv[2])
        return
    summaries = {}
    for mode in ("baseline", "cleanup"):
        p = subprocess.run([sys.executable, __file__, "--worker", mode], text=True, capture_output=True)
        (OUT / (mode + ".log")).write_text(p.stdout + "\nSTDERR:\n" + p.stderr)
        report = json.loads((OUT / (mode + ".json")).read_text()) if (OUT / (mode + ".json")).exists() else {}
        summaries[mode] = {"returncode": p.returncode, "status": report.get("status"), "measurements": report.get("measurements", []), "error": report.get("error")}
        print(json.dumps({"mode": mode, **summaries[mode]}, indent=2), flush=True)
    (OUT / "summary.json").write_text(json.dumps(summaries, indent=2))
    if any(v["returncode"] for v in summaries.values()):
        sys.exit(1)
if __name__ == "__main__":
    main()
