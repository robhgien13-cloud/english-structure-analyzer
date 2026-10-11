# Gold 55 — verification status (2026-10-11)

This document distinguishes three different checks:

1. **Real spaCy parser smoke**: the existing GitHub Actions workflow `Gold regression environment and special syntax smoke test` successfully parsed all 55 inputs and uploaded the raw outputs. A successful smoke run does **not** mean 55/55 correct S/V/O/C/M predictions.
2. **Local, in-sample gold comparison**: a separate local policy adapter (`convert`) was tested against those saved parser outputs and the reviewed gold annotation file. The reproducible local result was **55/55 sentences passing all explicitly annotated main-clause roles**. When missing gold roles were incorrectly interpreted as expected-empty, the result was **53/55**. In particular, G051–G055 omit some C/M annotations; omitted does not mean empty.
3. **GitHub adapter check**: `tests/gold55_school_grammar_adapter.py` is a separate experimental implementation. Its equivalence to the locally tested adapter, execution on all 55 real parser outputs, and exact gold agreement **have not been verified**. Do not advertise the 55/55 local metric as a GitHub adapter score.

Limitations: the 55 sentences were used while developing the rules, so this is an **in-sample** result. It does not establish generalization, full annotation completeness, or correctness on unseen sentences. The local adapter has not been merged into the deployed application.

Next gates:
- Verify that the GitHub adapter runs on all 55 real spaCy outputs.
- Commit the approved gold annotation fixture and a role-aware scorer (omitted fields excluded from scoring).
- Compare the exact same adapter implementation on GitHub and locally.
- Evaluate separately on newly approved, unseen challenge sentences.
- Do not merge into `main` before these checks pass and the user approves production integration.
