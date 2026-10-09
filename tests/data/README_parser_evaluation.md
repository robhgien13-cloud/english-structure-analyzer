# English parser evaluation corpus (draft)

This folder holds **40 candidate test sentences** and manually drafted school-grammar labels. It does not contain validated ground truth yet.

## Why a separate benchmark?
spaCy produces dependency heads/relations; benepar and SuPar produce constituency trees. Comparing raw labels is misleading. First compare whether each parser recovers the *same linguistically defined spans*: main subject skeleton, main verb, embedded clauses, and complements. A converter and a human-approved scoring protocol must be built separately.

## Status and limitations
- `parser_gold_40.json`: 40 draft cases grouped by syntax, all `review_status: pending`.
- `main.S` is the app's **diagnostic skeleton**, not the entire formal grammatical subject.
- `main.O` and `main.C` are **provisional school-grammar annotations**, particularly for clauses and non-finite complements.
- Existential, extraposition, coordination and embedded clauses need explicit adjudication rules.
- Do **not** report percentage accuracy before review and parser-specific span conversion are implemented.
- `python scripts/validate_parser_gold.py` checks basic consistency only.
- The production Flask/Render app is not modified by this experiment.

## Planned evaluation
1. Review ambiguous gold labels and add approved character offsets, allowing multiple valid answers.
2. Run all parsers in isolated GitHub Actions jobs and save raw parse output.
3. Convert outputs into the same canonical span schema.
4. Compute per-category precision/recall and inspect errors, separately from memory/time.
