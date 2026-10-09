"""Test SuPar non-BERT constituency model independently from production app."""
import json
import os
import resource
import sys
import time
import traceback
from pathlib import Path

os.environ["TOKENIZERS_PARALLELISM"] = "false"
OUT = Path("supar-test-results")
OUT.mkdir(exist_ok=True)
SENTENCES = [
    ["The", "man", "who", "smiled", "left", "."],
    ["When", "I", "arrived", "home", ",", "my", "mother", "was", "cooking", "dinner", "."],
    ["The", "book", "that", "my", "teacher", "recommended", "yesterday", "was", "surprisingly", "difficult", "to", "understand", "."],
    ["I", "found", "the", "book", "useful", "."],
    ["There", "are", "many", "books", "on", "the", "desk", "."],
    ["She", "gave", "me", "a", "book", "."],
]
report = {"model": "crf-con-en", "status": "started", "measurements": [], "results": []}

def sample(stage):
    info = {"stage": stage}
    with open("/proc/self/status", encoding="utf-8") as f:
        for line in f:
            if line.startswith(("VmRSS:", "VmHWM:")):
                key, val = line.split(":", 1)
                info[key + "_mb"] = round(int(val.strip().split()[0]) / 1024, 1)
    report["measurements"].append(info)
    (OUT / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

try:
    sample("start")
    import torch
    torch.set_num_threads(1)
    from supar import Parser
    sample("imports")
    parser = Parser.load("crf-con-en")
    sample("model_loaded")
    for i, tokens in enumerate(SENTENCES, 1):
        t0 = time.perf_counter()
        # Pretokenized input avoids loading Stanza tokenizer into RAM.
        dataset = parser.predict([tokens], verbose=False)
        tree = str(dataset.trees[0])
        report["results"].append({"sentence": " ".join(tokens), "tree": tree, "seconds": round(time.perf_counter()-t0, 3)})
        sample(f"parsed_{i}")
    report["status"] = "success"
except Exception:
    report["status"] = "failed"
    report["error"] = traceback.format_exc()
finally:
    sample("finished")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
if report["status"] != "success":
    sys.exit(1)
