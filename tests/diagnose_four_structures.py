"""Focused, non-blocking diagnostic for coordination, passive relative, negative inversion."""
import json
from pathlib import Path
from analyzer import EnglishStructureAnalyzer

CASES = {
"G038": ("She opened the door and entered the room.", ["opened", "entered"], "She"),
"G047": ("She opened the window, picked up her bag, and left the room without saying goodbye.", ["opened", "picked up", "left"], "She"),
"G048": ("The documents that had been sent yesterday were carefully examined by the manager.", ["were examined"], "The documents"),
"G051": ("Not until the final results were announced did the researchers realize how serious the problem had become.", ["did realize"], "the researchers"),
}
def run():
    analyzer = EnglishStructureAnalyzer()
    report = {}
    for cid, (sentence, verbs, subject) in CASES.items():
        result = analyzer.analyze(sentence)
        clauses = result["sentences"][0]["clauses"]
        main = next((c for c in clauses if c["type"] == "main"), None)
        actual_s = [v["text"] for v in main["core"]["S"]] if main else []
        actual_v = [v["text"] for v in main["core"]["V"]] if main else []
        missing = [v for v in verbs if not any(v.lower() == p.lower() for p in actual_v)]
        report[cid] = {"expected_main_subject": subject, "actual_main_subject":actual_s,
                       "expected_main_verbs":verbs,"actual_main_verbs":actual_v,
                       "subject_ok":subject in actual_s, "missing_verbs":missing,
                       "clauses":clauses}
        print(cid, "subject_ok",subject in actual_s,"missing_verbs",missing,flush=True)
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/focused-four-diagnostic.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__":run()
