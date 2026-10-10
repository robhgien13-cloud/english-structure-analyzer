"""Regression checks for adverbial-vs-nominal clause classification.
Run with en_core_web_sm installed. These are targeted checks, not accuracy claims.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyzer import EnglishStructureAnalyzer

analyzer = EnglishStructureAnalyzer()
examples = [
    ("When I arrived home, my mother was cooking dinner.", "cooking", "arrived"),
    ("Because it was raining, we stayed inside.", "stayed", "raining"),
    ("If you study hard, you will improve.", "improve", "study"),
    ("Although he was tired, he continued working.", "continued", "was"),
    ("I will call you after I finish my homework.", "call", "finish"),
]
for sentence, main_verb, subordinate_verb in examples:
    result = analyzer.analyze(sentence)["sentences"][0]
    tokens = {t["index"]: t for t in result["tokens"]}
    main = [c for c in result["clauses"] if c["type"] == "main"]
    assert len(main) == 1, (sentence, main)
    actual = tokens[main[0]["head_token"]]["text"]
    assert actual == main_verb, (sentence, actual, main_verb)
    assert any(c["type"] == "adverbial"
               and tokens[c["head_token"]]["text"] == subordinate_verb
               for c in result["clauses"]), (sentence, result["clauses"])
# When in an embedded nominal question must NOT be marked as adverbial.
result = analyzer.analyze("I know when she arrives.")["sentences"][0]
tokens = {t["index"]: t for t in result["tokens"]}
main = [c for c in result["clauses"] if c["type"] == "main"]
assert len(main) == 1 and tokens[main[0]["head_token"]]["text"] == "know"
assert not any(c["type"] == "adverbial" for c in result["clauses"])
print("Targeted adverbial/nominal regression checks passed.")
