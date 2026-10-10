"""Lightweight, independent syntax cues and conservative school-grammar checks.

This module does not replace spaCy predictions. It detects token-sequence cues
before SVOC conversion and reports potential inconsistencies without silently
changing the analysis. No additional model weights are required.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from spacy.matcher import Matcher


# School-grammar candidates; these are *not* exhaustive verb subcategorization.
VERB_FRAMES = {
    "allow": ("object_to_infinitive",),
    "ask": ("object_to_infinitive", "direct_object"),
    "decide": ("to_infinitive_object", "direct_object"),
    "find": ("object_adjective_complement", "direct_object"),
    "give": ("double_object", "direct_object"),
    "let": ("object_bare_infinitive",),
    "make": ("object_bare_infinitive", "object_adjective_complement"),
    "see": ("object_bare_infinitive", "direct_object"),
    "watch": ("object_bare_infinitive", "direct_object"),
}


@dataclass(frozen=True)
class SyntaxCue:
    kind: str
    start: int
    end: int
    text: str


def detect_syntax_cues(doc: Any) -> list[dict]:
    """Use surface patterns, not the predicted dependency tree."""
    matcher = Matcher(doc.vocab)
    matcher.add("CORRELATIVE_COMPARATIVE", [[
        {"LOWER": "the"},
        {"LOWER": {"IN": ["more", "less"]}},
        {"OP": "*"},
        {"IS_PUNCT": True},
        {"LOWER": "the"},
        {"LOWER": {"IN": ["more", "less"]}},
    ]])
    matcher.add("NO_SOONER_THAN", [[
        {"LOWER": "no"}, {"LOWER": "sooner"},
        {"OP": "*"}, {"LOWER": "than"},
    ]])
    matcher.add("NOT_UNTIL_INVERSION", [[
        {"LOWER": "not"}, {"LOWER": "until"},
        {"OP": "*"}, {"LOWER": {"IN": ["did", "does", "do", "had", "has", "have"]}},
    ]])
    # Keep one shortest match per cue type and start position.
    best: dict[tuple[str, int], SyntaxCue] = {}
    for match_id, start, end in matcher(doc):
        kind = doc.vocab.strings[match_id]
        cue = SyntaxCue(kind, start, end, doc[start:end].text)
        key = (kind, start)
        if key not in best or end < best[key].end:
            best[key] = cue
    return [asdict(c) for c in sorted(best.values(), key=lambda c: (c.start, c.end))]


def verb_frame_hints(doc: Any) -> list[dict]:
    hints = []
    for token in doc:
        lemma = token.lemma_.lower()
        if lemma in VERB_FRAMES and token.pos_ in {"VERB", "AUX"}:
            hints.append({"token_index": token.i, "verb": token.text,
                          "lemma": lemma, "candidate_frames": list(VERB_FRAMES[lemma])})
    return hints


def validate_school_core(core: dict, cues: list[dict]) -> list[dict]:
    """Flag potential conflicts; do not pretend a rule establishes gold SVOC."""
    issues = []
    roles = ("S", "V", "O", "C", "M")
    for role in roles:
        for item in core.get(role, []):
            if not isinstance(item, dict):
                continue
            tokens = set(item.get("token_ids", []))
            for other_role in roles:
                if other_role == role:
                    continue
                for other in core.get(other_role, []):
                    if not isinstance(other, dict):
                        continue
                    other_tokens = set(other.get("token_ids", []))
                    if tokens and tokens == other_tokens:
                        issues.append({"kind": "duplicate_core_span",
                                       "roles": [role, other_role],
                                       "token_ids": sorted(tokens)})
    if any(c["kind"] == "CORRELATIVE_COMPARATIVE" for c in cues):
        if any((e.get("text", "").lower().startswith("the more ") or
                e.get("text", "").lower().startswith("the less "))
               for e in core.get("O", []) if isinstance(e, dict)):
            issues.append({"kind": "possible_correlative_as_object",
                           "message": "Review the fronted comparative clause before using O for diagnosis."})
    # Deduplicate symmetric span reports.
    seen = set()
    unique = []
    for issue in issues:
        key = (issue["kind"], tuple(sorted(issue.get("roles", []))),
               tuple(issue.get("token_ids", [])))
        if key not in seen:
            unique.append(issue)
            seen.add(key)
    return unique
