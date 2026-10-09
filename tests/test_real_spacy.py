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
