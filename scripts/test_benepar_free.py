"""Isolated benepar CPU feasibility experiment; does not modify the web app."""
import json, os, resource, time, traceback
from pathlib import Path

SENTENCES = [
    "The man who smiled left.",
    "When I arrived home, my mother was cooking dinner.",
    "The book that my teacher recommended yesterday was surprisingly difficult to understand.",
]
OUT = Path("benepar-test-results")
OUT.mkdir(exist_ok=True)
def rss_mb():
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
def save(data):
    (OUT / "results.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
def main():
    result = {"model": "benepar_en3", "limit_mb": 512, "cases": [], "status": "started"}
    save(result)
    try:
        import spacy, benepar
        import torch
        torch.set_num_threads(1)
        result["versions"] = {"spacy": spacy.__version__, "torch": torch.__version__}
        t = time.perf_counter()
        benepar.download("benepar_en3")
        result["download_seconds"] = round(time.perf_counter() - t, 2)
        result["after_download_rss_mb"] = rss_mb()
        nlp = spacy.blank("en")
        nlp.add_pipe("sentencizer")
        t = time.perf_counter()
        nlp.add_pipe("benepar", config={"model": "benepar_en3"})
        result["load_seconds"] = round(time.perf_counter() - t, 2)
        result["after_load_rss_mb"] = rss_mb()
        for s in SENTENCES:
            t = time.perf_counter()
            doc = nlp(s)
            result["cases"].append({"text": s, "parse": list(doc.sents)[0]._.parse_string,
                "seconds": round(time.perf_counter() - t, 3), "peak_rss_mb": rss_mb()})
            save(result)
        result["status"] = "success"
    except Exception:
        result["status"] = "failed"
        result["error"] = traceback.format_exc()
        print(result["error"], flush=True)
        raise
    finally:
        result["peak_rss_mb"] = rss_mb()
        result["under_512mb_observed"] = result["peak_rss_mb"] <= 512
        save(result)
        print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)
if __name__ == "__main__":
    main()
