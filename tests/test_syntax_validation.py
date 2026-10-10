import unittest

import spacy
from syntax_validation import detect_syntax_cues, verb_frame_hints, validate_school_core


class SyntaxValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nlp = spacy.blank("en")

    def test_comparative_surface_cue_without_parser(self):
        doc = self.nlp("The more carefully we examined the document, the less convincing its explanation became.")
        self.assertTrue(any(c["kind"] == "CORRELATIVE_COMPARATIVE"
                            for c in detect_syntax_cues(doc)))

    def test_no_sooner_surface_cue_without_parser(self):
        doc = self.nlp("No sooner had the committee announced its decision than several members raised objections.")
        self.assertTrue(any(c["kind"] == "NO_SOONER_THAN"
                            for c in detect_syntax_cues(doc)))

    def test_comparative_object_conflict(self):
        cues = [{"kind": "CORRELATIVE_COMPARATIVE"}]
        core = {"S": [], "V": [], "O": [{"text": "The more carefully we examined the document",
                                        "token_ids": [1, 2, 3]}], "C": [], "M": []}
        issues = validate_school_core(core, cues)
        self.assertIn("possible_correlative_as_object", {x["kind"] for x in issues})

    def test_duplicate_core_span(self):
        core = {"S": [{"token_ids": [1, 2]}], "V": [], "O": [],
                "C": [{"token_ids": [1, 2]}], "M": []}
        issues = validate_school_core(core, [])
        self.assertIn("duplicate_core_span", {x["kind"] for x in issues})


if __name__ == "__main__":
    unittest.main()
