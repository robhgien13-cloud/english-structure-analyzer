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

    def test_not_until_inversion_surface_cue(self):
        doc = self.nlp("Not until the report was published did the researchers understand the result.")
        self.assertTrue(any(c["kind"] == "NOT_UNTIL_INVERSION"
                            for c in detect_syntax_cues(doc)))

    def test_negative_no_sooner_case(self):
        doc = self.nlp("The team had no sooner arrived than the storm began.")
        self.assertFalse(any(c["kind"] == "NO_SOONER_THAN"
                             for c in detect_syntax_cues(doc)))

    def test_no_conflict_on_distinct_spans(self):
        core = {"S": [{"token_ids": [1]}], "V": [{"token_ids": [2]}],
                "O": [{"token_ids": [3]}], "C": [], "M": []}
        self.assertEqual(validate_school_core(core, []), [])

    def test_verb_frames_with_real_spacy(self):
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.skipTest("spaCy English model not installed")
        doc = nlp("She allowed him to leave and found the answer useful.")
        hints = verb_frame_hints(doc)
        lemmas = {h["lemma"] for h in hints}
        self.assertTrue({"allow", "find"}.issubset(lemmas))


if __name__ == "__main__":
    unittest.main()
