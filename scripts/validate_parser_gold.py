"""Validate candidate gold corpus; never label unreviewed examples as accuracy scores."""
import json
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"tests"/"data"/"parser_gold_40.json"
d=json.loads(p.read_text(encoding="utf-8"))
assert len(d["cases"])==40
assert len({x["id"] for x in d["cases"]})==40
for c in d["cases"]:
    assert c["review_status"] in ("pending","approved","rejected")
    text=c["text"]
    for key in ("S","V","C"):
        value=c["main"][key]
        if value is not None:
            assert value in text, (c["id"],key,value)
    for val in c["main"]["O"]+c["embedded_spans"]:
        assert val in text,(c["id"],val)
print("Validated 40 candidate sentences; gold remains human-review pending.")
