"""Integration checks using the real spaCy English model.

These checks deliberately separate stable SVOC expectations from structural
smoke tests, since parsing can vary with spaCy/model versions.
"""
import unittest

from analyzer import EnglishStructureAnalyzer


class RealSpacyIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = EnglishStructureAnalyzer()

    def analyze_one(self, text):
        result = self.analyzer.analyze(text)
        self.assertEqual(len(result["sentences"]), 1, text)
        sentence = result["sentences"][0]
        self.assertTrue(sentence["tokens"], text)
        self.assertTrue(sentence["clauses"], text)
        self.assertTrue(any(c["type"] == "main" for c in sentence["clauses"]), text)
        return sentence

    def test_core_svoc(self):
        cases = [
            ("She is happy.", {"S": ["She"], "V": ["is"], "O": [], "C": ["happy"]}),
            ("I gave him a present.", {"S": ["I"], "V": ["gave"], "O": ["him", "a present"], "C": []}),
            ("When I arrived home, my mother was cooking dinner.",
             {"S": ["my mother"], "V": ["was cooking"], "O": ["dinner"], "C": []}),
            ("The letter was written yesterday.",
             {"S": ["The letter"], "V": ["was written"], "O": [], "C": []}),
            ("She will come tomorrow.",
             {"S": ["She"], "V": ["will come"], "O": [], "C": []}),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                sentence = self.analyze_one(text)
                core = next(c["core"] for c in sentence["clauses"] if c["type"] == "main")
                for role, values in expected.items():
                    self.assertEqual([e["text"] for e in core[role]], values, (text, role))

    def test_complex_sentence_structure(self):
        """Check structural meaning, not just whether parsing completes."""
        cases = [
            {
                "text": "The man who smiled left.",
                "main_subject": "The man",
                "main_verb": "left",
                "required_clause_type": "relative",
            },
            {
                "text": "If it rains, we will stay home.",
                "main_subject": "we",
                "main_verb": "will stay",
                "required_clause_type": "adverbial",
            },
            {
                "text": "I found the book useful.",
                "main_subject": "I",
                "main_verb": "found",
                "main_object": "the book",
                "main_complement": "useful",
            },
            {
                "text": "They painted the door red.",
                "main_subject": "They",
                "main_verb": "painted",
                "main_object": "the door",
                "main_complement": "red",
            },
        ]
        for case in cases:
            with self.subTest(text=case["text"]):
                sentence = self.analyze_one(case["text"])
                main = next(c for c in sentence["clauses"] if c["type"] == "main")
                core = main["core"]
                diagnostic = {"clauses": [{"type": c["type"], "text": c["text"], "core": c["core"]} for c in sentence["clauses"]], "tokens": [{"text": t["text"], "head": t["head"], "deprel": t["deprel"]} for t in sentence["tokens"]]}
                self.assertIn(case["main_subject"], [e["text"] for e in core["S"]], diagnostic)
                self.assertIn(case["main_verb"], [e["text"] for e in core["V"]], diagnostic)
                if "main_object" in case:
                    self.assertIn(case["main_object"], [e["text"] for e in core["O"]], diagnostic)
                if "main_complement" in case:
                    self.assertIn(case["main_complement"], [e["text"] for e in core["C"]], diagnostic)
                if "required_clause_type" in case:
                    self.assertIn(case["required_clause_type"],
                                  [c["type"] for c in sentence["clauses"]])


    def test_experiment_c_syntax_diagnostics(self):
        """Exercise C on the CI path that runs real-spaCy integration tests."""
        cases = [
            ("The more carefully we examined the document, the less convincing its explanation became.",
             "CORRELATIVE_COMPARATIVE"),
            ("No sooner had the committee announced its decision than several members raised objections.",
             "NO_SOONER_THAN"),
            ("Not until the final report was published did the researchers realize the truth.",
             "NOT_UNTIL_INVERSION"),
        ]
        for text, expected_cue in cases:
            with self.subTest(text=text):
                sentence = self.analyze_one(text)
                diagnostic = sentence.get("syntax_validation")
                self.assertIsInstance(diagnostic, dict)
                self.assertIn(expected_cue, {c["kind"] for c in diagnostic["cues"]})
                self.assertIn(diagnostic["status"], {"unverified", "review"})

        sentence = self.analyze_one("She allowed him to leave and found the answer useful.")
        hints = sentence["syntax_validation"]["verb_frame_hints"]
        self.assertTrue({"allow", "find"}.issubset({h["lemma"] for h in hints}))


    def test_experiment_c_negative_controls(self):
        """No positive cue should be emitted for superficially similar sentences."""
        negatives = [
            "The more careful student finished the assignment.",
            "No sooner option was available to the committee.",
            "The researchers did not wait until the report was published.",
            "She gave him more time than he expected.",
            "The less expensive option was selected.",
        ]
        for text in negatives:
            with self.subTest(text=text):
                sentence = self.analyze_one(text)
                self.assertEqual(sentence["syntax_validation"]["cues"], [], text)


    def test_experiment_c_coverage_report(self):
        """Publish transparent cue coverage, including unsupported syntax types."""
        from scripts.report_experiment_c_coverage import main
        report = main()
        self.assertEqual(report["positives"], 10)
        self.assertEqual(report["negatives"], 8)
        self.assertEqual(len(report["details"]["positive"]), 10)
        self.assertEqual(len(report["details"]["negative"]), 8)

    def test_diverse_sentence_smoke(self):
        sentences = [
            "I want to leave.",
            "The man who smiled left.",
            "They painted the door red.",
            "Open the door.",
            "There are books on the table.",
            "She sang and danced.",
            "If it rains, we will stay home.",
            "The book that I bought was expensive.",
            "Having finished his work, he went home.",
            "Never have I seen such a thing.",
            "I found the book useful.",
            "The cake was eaten by the children.",
            "He said that she was right.",
            "She is reading a book.",
            "Although he was tired, he kept working.",
        ]
        for text in sentences:
            with self.subTest(text=text):
                self.analyze_one(text)


if __name__ == "__main__":
    unittest.main()
