"""Regression tests for syntax conversion, independent of model installation."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location('analyzer_under_test', Path(__file__).parents[1] / 'analyzer.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
with patch.dict(sys.modules, {'spacy': SimpleNamespace()}):
    spec.loader.exec_module(module)


def parse(rows):
    tokens = [SimpleNamespace(i=i, text=text, lemma_=lemma, pos_=pos,
                              tag_=tag, dep_=dep, children=[])
              for i, (text, lemma, pos, tag, dep, head) in enumerate(rows)]
    for token, row in zip(tokens, rows):
        token.head = tokens[row[-1]]
        if token.head is not token:
            token.head.children.append(token)

    class Span(list):
        text = ' '.join(t.text for t in tokens)

    analyzer = module.EnglishStructureAnalyzer.__new__(module.EnglishStructureAnalyzer)
    sentence = analyzer._convert_sentence(Span(tokens))
    return analyzer._sentence(sentence, 1)


def main(sentence):
    return next(c for c in sentence['clauses'] if c['type'] == 'main')['core']


class AnalyzerRegressionTests(unittest.TestCase):
    def test_pronoun_copular_complement_is_preserved(self):
        sentence = parse([
            ('It', 'it', 'PRON', 'PRP', 'nsubj', 1),
            ('is', 'be', 'AUX', 'VBZ', 'ROOT', 1),
            ('me', 'I', 'PRON', 'PRP', 'attr', 1),
        ])
        self.assertEqual([c['text'] for c in main(sentence)['C']], ['me'])

    def test_verbal_open_complement_remains_a_clause(self):
        sentence = parse([
            ('I', 'I', 'PRON', 'PRP', 'nsubj', 1),
            ('made', 'make', 'VERB', 'VBD', 'ROOT', 1),
            ('him', 'he', 'PRON', 'PRP', 'dobj', 1),
            ('leave', 'leave', 'VERB', 'VB', 'xcomp', 1),
        ])
        self.assertEqual(len(sentence['clauses']), 2)
        self.assertEqual(len(main(sentence)['C']), 1)
        self.assertIn('clause_ref', main(sentence)['C'][0])

    def test_copular_adjective_has_one_complement_and_relation(self):
        sentence = parse([
            ('She', 'she', 'PRON', 'PRP', 'nsubj', 1),
            ('is', 'be', 'AUX', 'VBZ', 'ROOT', 1),
            ('happy', 'happy', 'ADJ', 'JJ', 'acomp', 1),
        ])
        self.assertEqual([c['text'] for c in main(sentence)['C']], ['happy'])
        self.assertEqual(len([r for r in sentence['relations'] if r['type'] == 'complements']), 1)

    def test_relative_clause_does_not_duplicate_main_complement(self):
        sentence = parse([
            ('The', 'the', 'DET', 'DT', 'det', 1),
            ('boy', 'boy', 'NOUN', 'NN', 'nsubj', 5),
            ('who', 'who', 'PRON', 'WP', 'nsubj', 4),
            ('is', 'be', 'AUX', 'VBZ', 'aux', 4),
            ('running', 'run', 'VERB', 'VBG', 'relcl', 1),
            ('is', 'be', 'AUX', 'VBZ', 'ROOT', 5),
            ('my', 'my', 'PRON', 'PRP$', 'poss', 7),
            ('brother', 'brother', 'NOUN', 'NN', 'attr', 5),
        ])
        self.assertEqual([c['text'] for c in main(sentence)['C']], ['my brother'])
        self.assertEqual(len(sentence['clauses']), 2)

    def test_object_complement_parse_variants(self):
        for dep, book_head in [('oprd', 1), ('ccomp', 4), ('xcomp', 4)]:
            with self.subTest(dep=dep):
                sentence = parse([
                    ('I', 'I', 'PRON', 'PRP', 'nsubj', 1),
                    ('found', 'find', 'VERB', 'VBD', 'ROOT', 1),
                    ('the', 'the', 'DET', 'DT', 'det', 3),
                    ('book', 'book', 'NOUN', 'NN', 'dobj' if book_head == 1 else 'nsubj', book_head),
                    ('useful', 'useful', 'ADJ', 'JJ', dep, 1),
                ])
                core = main(sentence)
                self.assertEqual({r: [e['text'] for e in core[r]] for r in 'SVOC'},
                                 {'S': ['I'], 'V': ['found'], 'O': ['the book'], 'C': ['useful']})
                self.assertEqual(core['C'][0]['complement_of'], 'O')
                self.assertEqual(len(sentence['clauses']), 1)
                relation = next(r for r in sentence['relations'] if r['type'] == 'complements')
                self.assertEqual(relation['target'], core['O'][0]['id'])

    def test_initial_adverbial_clause_preserves_main_subject(self):
        for mistaken_root in [False, True]:
            with self.subTest(mistaken_root=mistaken_root):
                sentence = parse([
                    ('When', 'when', 'SCONJ', 'WRB', 'mark', 2),
                    ('I', 'I', 'PRON', 'PRP', 'nsubj', 2),
                    ('arrived', 'arrive', 'VERB', 'VBD', 'ROOT' if mistaken_root else 'advcl', 2 if mistaken_root else 8),
                    ('home', 'home', 'NOUN', 'NN', 'npadvmod', 2),
                    (',', ',', 'PUNCT', ',', 'punct', 2),
                    ('my', 'my', 'PRON', 'PRP$', 'poss', 6),
                    ('mother', 'mother', 'NOUN', 'NN', 'nsubj', 8),
                    ('was', 'be', 'AUX', 'VBD', 'aux', 8),
                    ('cooking', 'cook', 'VERB', 'VBG', 'advcl' if mistaken_root else 'ROOT', 2 if mistaken_root else 8),
                    ('dinner', 'dinner', 'NOUN', 'NN', 'dobj', 8),
                ])
                core = main(sentence)
                self.assertEqual([s['text'] for s in core['S']], ['my mother'])
                self.assertEqual([v['text'] for v in core['V']], ['was cooking'])
                adverbial = next(c for c in sentence['clauses'] if c['type'] == 'adverbial')
                self.assertEqual([s['text'] for s in adverbial['core']['S']], ['I'])
                self.assertEqual(sentence['warnings'], [])

    def test_finite_complement_keeps_its_subject(self):
        sentence = parse([
            ('I', 'I', 'PRON', 'PRP', 'nsubj', 1),
            ('found', 'find', 'VERB', 'VBD', 'ROOT', 1),
            ('she', 'she', 'PRON', 'PRP', 'nsubj', 3),
            ('was', 'be', 'AUX', 'VBD', 'ccomp', 1),
            ('happy', 'happy', 'ADJ', 'JJ', 'acomp', 3),
        ])
        self.assertEqual(main(sentence)['C'], [])
        self.assertEqual(len(sentence['clauses']), 2)


if __name__ == '__main__':
    unittest.main()
