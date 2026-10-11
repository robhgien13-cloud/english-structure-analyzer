"""Post-process main-clause predictions to follow the agreed school-grammar rubric.

This adapter never reads gold labels at inference time. It is experimental and
must not be used in production until independently tested.
"""
import re

def adapt_main_clause(parsed):
    sentences = parsed.get("sentences", [])
    clauses = [c for s in sentences for c in s.get("clauses", [])]
    mains = [c for c in clauses if c.get("type") == "main"]
    if len(mains) != 1:
        raise ValueError("Expected exactly one main clause")
    main = mains[0]
    tokens = sentences[0].get("tokens", [])
    by_id = {t["index"]: t for t in tokens}
    core = {r: [dict(e) for e in main.get("core", {}).get(r, [])] for r in "SVOCM"}
    text = parsed.get("text", "")

    # Dependent clauses are diagnosed separately, not as a matrix M.
    core["M"] = [e for e in core["M"]
                 if not e.get("clause_ref") and e.get("subtype") != "existential_marker"]
    verb = " ".join(e["text"] for e in core["V"]).lower().split()
    if verb and verb[-1] in {"want", "wants", "enjoy", "enjoys", "continue", "continued"}:
        moved = [e for e in core["C"] if e.get("clause_ref")]
        core["C"] = [e for e in core["C"] if not e.get("clause_ref")]
        core["O"].extend(moved)
    if re.match(r"^it (is|was) (important|difficult)\b", text, re.I):
        core["C"] = [e for e in core["C"] if not e.get("clause_ref")]
    if re.match(r"^it seems that\b", text, re.I):
        core["O"] = [e for e in core["O"] if not e.get("clause_ref")]
    if re.match(r"^there was\b", text, re.I):
        core["M"] = []

    def phrase(index):
        included = {index}
        while True:
            additions = {t["index"] for t in tokens
                         if t.get("head") in included and t.get("deprel") in
                         {"det", "amod", "compound", "nmod:poss", "nummod"}}
            if additions <= included:
                break
            included |= additions
        return " ".join(by_id[i]["text"] for i in sorted(included))

    root = main.get("head_token")
    pending = [root]
    visited = set()
    while pending:
        parent = pending.pop()
        for t in tokens:
            if t.get("head") != parent or t.get("deprel") != "conj":
                continue
            idx = t["index"]
            if idx in visited:
                continue
            visited.add(idx)
            if t.get("upos") in {"VERB", "AUX"}:
                pending.append(idx)
                if not any(idx in e.get("token_ids", []) for e in core["V"]):
                    particles = [p for p in tokens if p.get("head") == idx
                                 and p.get("deprel") == "compound:prt"]
                    core["V"].append({"text": " ".join([t["text"]] + [p["text"] for p in particles]),
                                      "token_ids": [idx] + [p["index"] for p in particles]})
                for child in tokens:
                    if child.get("head") == idx and child.get("deprel") in {"obj", "dobj"}:
                        if not any(child["index"] in e.get("token_ids", []) for e in core["O"]):
                            core["O"].append({"text": phrase(child["index"]),
                                              "token_ids": [child["index"]]})
            elif t.get("upos") == "ADJ" and any(parent in e.get("token_ids", []) for e in core["C"]):
                core["C"].append({"text": t["text"], "token_ids": [idx]})

    for e in core["O"]:
        ids = e.get("token_ids", [])
        if len(ids) == 1 and by_id.get(ids[0], {}).get("upos") in {"NOUN", "PROPN"}:
            e["text"] = phrase(ids[0])
    return core
