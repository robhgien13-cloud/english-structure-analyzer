"""Adapt actual experiment_spacy_40.py output to candidate comparison schema."""
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/"parser-40-results/spacy-app-normalized.json"
if not source.is_file():
    raise SystemExit("Missing real parser output: "+str(source))
rows=json.loads(source.read_text(encoding="utf-8"))
predictions=[]
for row in rows:
    main={}
    for role in ("S","V","O","C"):
        values=row.get("pred_"+role)
        if not isinstance(values,list):
            continue
        # A prediction can legitimately be empty, but missing fields are not scored.
        main[role]=values
    predictions.append({"id":row["id"],"main":main})
dest=ROOT/"parser-40-results/candidate-predictions.json"
dest.write_text(json.dumps({"results":predictions},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
subprocess.run([sys.executable,str(ROOT/"scripts/compare_gold_candidate_40.py"),
                "--predictions",str(dest)],check=True)
