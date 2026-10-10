"""Experiment C: fixed, auditable detection coverage report (not SVOC accuracy)."""
import json
from analyzer import EnglishStructureAnalyzer

CASES = [
    ("H071", "No sooner had the committee announced its decision than several members raised objections.", "NO_SOONER_THAN"),
    ("H072", "Not until the final report was published did the researchers realize how much evidence had been overlooked.", "NOT_UNTIL_INVERSION"),
    ("H073", "Were the proposal to be rejected, the company would need to reconsider its strategy.", "INVERTED_CONDITIONAL"),
    ("H078", "So difficult was the examination that few candidates managed to complete it on time.", "SO_THAT_INVERSION"),
    ("H079", "The more carefully we examined the document, the less convincing its explanation became.", "CORRELATIVE_COMPARATIVE"),
    ("P006", "The harder you work, the better your results will be.", "CORRELATIVE_COMPARATIVE"),
    ("P007", "The faster he ran, the more exhausted he became.", "CORRELATIVE_COMPARATIVE"),
    ("P008", "Not until yesterday did I understand the problem.", "NOT_UNTIL_INVERSION"),
    ("P009", "Hardly had we arrived when the rain began.", "HARDLY_WHEN"),
    ("P010", "Only after the meeting did she reveal her decision.", "ONLY_AFTER_INVERSION"),
]
NEGATIVES = [
    "The more careful student finished the assignment.",
    "No sooner option was available to the committee.",
    "The researchers did not wait until the report was published.",
    "She gave him more time than he expected.",
    "The less expensive option was selected.",
    "The more the merrier was their motto.",
    "He had no sooner option than waiting.",
    "The team met after the meeting.",
]

def main():
    analyzer = EnglishStructureAnalyzer()
    positive = []
    negative = []
    for case_id, sentence, expected in CASES:
        result = analyzer.analyze(sentence)["sentences"][0]["syntax_validation"]
        actual = sorted({cue["kind"] for cue in result["cues"]})
        positive.append({"id": case_id, "expected": expected, "actual": actual,
                         "detected": expected in actual})
    for sentence in NEGATIVES:
        result = analyzer.analyze(sentence)["sentences"][0]["syntax_validation"]
        actual = sorted({cue["kind"] for cue in result["cues"]})
        negative.append({"sentence": sentence, "actual": actual, "false_positive": bool(actual)})
    report = {
        "metric": "surface cue detection only; not SVOC correctness",
        "positives": len(positive),
        "detected": sum(x["detected"] for x in positive),
        "negatives": len(negative),
        "false_positives": sum(x["false_positive"] for x in negative),
        "details": {"positive": positive, "negative": negative},
    }
    print("EXPERIMENT C COVERAGE:", json.dumps(report, ensure_ascii=False))
    return report

if __name__ == "__main__":
    main()
