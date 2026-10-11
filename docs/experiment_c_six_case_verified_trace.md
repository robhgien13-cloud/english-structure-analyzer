# Experiment C — verified six-case dependency trace (2026-10-11)

Evidence: [successful workflow run 38097407582](https://github.com/robhgien13-cloud/english-structure-analyzer/actions/runs/38097407582), artifact `experiment-c-six-case-trace` (ID 11686566608). Real `en_core_web_sm` model, not fabricated fixtures. **No parser changes made.** Gold candidate remains unapproved.

| ID | Raw spaCy dependency | Normalized dependency | Actual main core | Mechanism |
|---|---|---|---|---|
| G019 | working: xcomp→continued | xcomp unchanged | O=[], C=[working] | `_build_clause` treats most xcomp as C; expected O=[working] |
| G028 | learn: xcomp→is; important: acomp→is | unchanged | C=[important, to learn English] | extraposed infinitive not separated from C; expected C=[important] and real_subject=to learn English |
| G029 | is: ccomp→seems | unchanged | O=[that he is honest], C=[] | extraposed ccomp condition requires matrix C for seem, absent here; agreed convention real_subject |
| G031 | become: xcomp→wants | unchanged | O=[], C=[to become a doctor] | `want + to-infinitive` not among xcomp-to-O exceptions |
| G034 | playing: xcomp→enjoy | unchanged | O=[], C=[playing tennis] | `enjoy + gerund` not among xcomp-to-O exceptions |
| G040 | difficult: acomp→was; surprisingly: advmod→difficult; understand: xcomp→difficult | unchanged | C=[difficult] | `_complements` extracts core adjective, not its full modifier/infinitive span |

All six raw dependencies above are confirmed by downloaded workflow artifact; for these specific tokens the app's normalized dependency labels are unchanged except that spaCy ROOT is normalized to root. This does **not** prove spaCy's linguistic analysis is universally correct. Classification issues arise at the conversion from dependencies to school grammar.

## Safe proposed implementation (not yet applied)

1. For G019, G031 and G034, implement verb-frame-sensitive xcomp mapping only after checking token lemma, infinitive/gerund morphology and whether an explicit matrix object is present. Include negative examples: `I found the book useful`, `She wants him to leave`, `I watched him leave`.
2. For G028, retain formal subject It and attach `to learn English` as a separate `real_subject` relation, not a matrix C; preserve the embedded O=English.
3. For G029, explicitly handle formal It + seem + that-clause as real-subject-equivalent under project convention, with ambiguity annotation; do not apply to `I think that ...`.
4. For G040, retain `C.core=difficult` while adding `C.full=surprisingly difficult to understand`; preserve modifier attachment and the understood object coreference to book.
5. Add six positive cases and contrastive negatives; run existing test suites and all 40 cases. Keep G038/G039 coordination separately tracked: current 160-role comparison cannot certify those.

## Scope

This is a trace report, **not** a claim of 94.4% grammatical accuracy. The 151/160 value measures exact role-field string agreement with an unapproved candidate. No existing gold, parser, main or production was edited.
