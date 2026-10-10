"""Diagnostic-only investigation of nominal-clause parsing. No production changes."""
import spacy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyzer import EnglishStructureAnalyzer
examples = [
    "What he said surprised everyone.",
    "That he passed the exam is surprising.",
    "Whether she will come remains uncertain.",
    "What she bought was expensive.",
    "I know what he said.",
    "I wonder whether she will come.",
    "The book that he bought surprised everyone.",
    "When he arrived, everyone stood up.",
]
nlp = spacy.load("en_core_web_sm")
app = EnglishStructureAnalyzer()
for sentence in examples:
    print("\nCASE:", sentence)
    print("RAW:", [(t.text, t.pos_, t.tag_, t.dep_, t.head.text) for t in nlp(sentence)])
    result = app.analyze(sentence)["sentences"][0]
    print("NORMALIZED:", [(t["text"], t["deprel"], t["head"]) for t in result["tokens"]])
    print("CLAUSES:", [(c["type"], c["text"], {k:[e["text"] for e in v] for k,v in c["core"].items() if v}) for c in result["clauses"]])

# Assertions for unambiguous school-grammar clause roles.
def main_core(text):
    clauses = app.analyze(text)["sentences"][0]["clauses"]
    main = next(c for c in clauses if c["type"] == "main")
    return clauses, {k: [e["text"] for e in v] for k, v in main["core"].items()}

clauses, core = main_core("What he said surprised everyone.")
assert core["S"] == ["What he said"], core
assert core["V"] == ["surprised"], core
assert core["O"] == ["everyone"], core
assert any(c["type"] == "nominal-subject" and
           [e["text"] for e in c["core"]["S"]] == ["he"] and
           [e["text"] for e in c["core"]["V"]] == ["said"]
           for c in clauses), clauses
for text in ("That he passed the exam is surprising.",
             "Whether she will come remains uncertain.",
             "What she bought was expensive."):
    _, core = main_core(text)
    assert len(core["S"]) == 1, (text, core)
print("NOMINAL ASSERTIONS PASSED")
