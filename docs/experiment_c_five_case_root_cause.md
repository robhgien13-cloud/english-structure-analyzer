# Experiment C: five mismatch sentences — cause hypotheses and safe correction design

Status: **diagnostic proposal only**. No parser, gold, experiments A/B, main or production changes. Evidence: GitHub Actions run 38097216782 (commit 8c9d7390), 40-case candidate comparison: 151/160 role-string matches, 9 mismatches in G019/G028/G029/G031/G034/G040 (six sentences, not five). Existing gold candidate is unapproved; these are not accuracy scores.

## Important correction to prior summary

The mismatches are in **six** cases, not five: G019, G028, G029, G031, G034, G040. Counts: 2+1+1+2+2+1 = 9 role mismatches. Do not conflate a role-level mismatch with an independently established grammatical error.

## Code inspection and likely causes

The observations below are **source-based hypotheses** pending targeted token/dependency trace, not proven spaCy causes.

1. **G019 — Although he was tired, he continued working.** Expected O=working, C=empty; predicted O missing, C=working. In `analyzer.py`, `_build_clause` classifies direct child `xcomp` as C by default, with a narrow O exception for `decide + to`. An `xcomp` headed by gerund `working` following `continue` may therefore be classified as C. Candidate remedy: lexical-frame-aware treatment of gerund complements, keeping an explicit uncertainty flag for verbs allowing multiple constructions.

2. **G028 — It is important to learn English.** Expected C=important; predicted C includes `to learn English`. `_build_clause` uses C as default for `xcomp` and its extraposition special case only recognizes `ccomp` introduced by `that/whether`, not an extraposed infinitive. Candidate remedy: store formal `It`, true subject infinitive and its internal roles in separate structured relations; avoid promoting true subject to matrix C.

3. **G029 — It seems that he is honest.** Expected O empty; predicted O includes that clause. Existing `extraposed` logic for `ccomp` checks `seem` only when `core['C']` is nonempty; G029 has no C. Under the **approved project convention** treat It as formal S, that-clause as real-subject-equivalent, with alternate analyses flagged. Candidate remedy: narrow explicit seem+It+that rule; don't generalize all seem complements.

4. **G031 — She wants to become a doctor.** Expected O=to become a doctor, C empty; predicted O missing, C present. `xcomp` defaults to C except a narrow `decide` rule. Candidate remedy: explicitly distinguish `want + to-infinitive` (matrix O) from `want + O + to-infinitive` (SVOC); preserve embedded C=a doctor.

5. **G034 — I enjoy playing tennis.** Expected O=playing tennis, C empty; predicted O missing, C present. `xcomp` defaults to C; add a lexical frame for `enjoy + gerund` as matrix O, with nested O=tennis.

6. **G040 — The book that my teacher recommended yesterday was surprisingly difficult to understand.** Expected C full phrase; predicted C core only. `_complements` relies on `_element` → `_phrase_text` → `_phrase_ids`, which intentionally collects selected NP modifiers, not all adjective modifiers or attached infinitives. Candidate remedy: keep `C.core=difficult`, `C.full=surprisingly difficult to understand`, with explicit degree adverb and infinitive relations; don't change core to an undifferentiated long span.

## Required evidence before code modification

- For each case, capture spaCy token index/text/POS/dependency/head and normalized dependency, matrix and embedded `core`, `syntax_validation` issues, and expected candidate fields.
- Check G019/G031/G034 dependency label of complement (`xcomp` vs other), and that the proposed rule does not misclassify causative/perception SVOC.
- For G028/G029 distinguish `It is ADJ to ...`, `It seems that ...`, `I think that ...`, `It was John that ...`.
- For G040 compare C.core and C.full without losing modifier attachments or implicit-object link to book.
- Run 40-case comparison **and** existing regression suites before accepting any code changes. Compare actual prediction output, not synthetic fixtures.
- G038/G039 coordination completeness is **not tested** by the current 160 role-cell comparison, despite no mismatch in that aggregate.

## Suggested order and approval gate

1. Add **read-only diagnostic tracing** on the C branch; save a reproducible report.
2. Review trace and write a minimal patch plan with explicit positive/negative examples.
3. Only then, if authorized, modify **C branch code** and run regression tests. Never change existing gold JSON without explicit approval.
