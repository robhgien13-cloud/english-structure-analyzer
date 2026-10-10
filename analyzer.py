from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Set
import spacy

CLAUSE_RELS = {'root','advcl','ccomp','xcomp','acl','acl:relcl','csubj','csubj:pass','parataxis'}
SUBJECT_RELS = {'nsubj','nsubj:pass','csubj','csubj:pass'}
OBJECT_RELS = {'obj','iobj'}
MOD_RELS = {'advmod','advcl','obl','obl:tmod','npmod','discourse'}
NP_EXPAND = {'predet','det','amod','compound','nummod','nmod','nmod:poss','case','fixed','flat','appos'}
AUX_RELS = {'aux','aux:pass','cop','compound:prt','neg'}
REL_WORDS = {'who','whom','whose','which','that','where','when','why'}

@dataclass
class IdFactory:
    sent: int
    counters: Dict[str, int]
    def make(self, kind: str) -> str:
        self.counters[kind] = self.counters.get(kind, 0) + 1
        return f'S{self.sent:02d}-{kind.upper()}-{self.counters[kind]:03d}'

@dataclass
class Word:
    id: int
    text: str
    lemma: str
    upos: str
    xpos: str
    head: int
    deprel: str

@dataclass
class Sentence:
    text: str
    words: List[Word]

class EnglishStructureAnalyzer:
    def __init__(self):
        # Disable NER because this viewer only needs syntax/POS/lemmatization.
        self.nlp = spacy.load('en_core_web_sm', disable=['ner'])

    def _convert_sentence(self, span) -> Sentence:
        """Convert spaCy's parse to the UD-like shape used by the existing viewer."""
        tokens = list(span)
        overrides = {}

        # spaCy attaches a preposition to the governor and its object below it.
        # The old Stanza/UD-oriented code expects the nominal as obl and the
        # preposition as case, so normalize that small structural difference.
        for tok in tokens:
            if tok.dep_ == 'prep':
                pobj = next((c for c in tok.children if c.dep_ == 'pobj'), None)
                if pobj is not None:
                    overrides[tok.i] = ('case', pobj.i + 1)
                    overrides[pobj.i] = ('obl', tok.head.i + 1)

        # Passive agents: spaCy uses agent -> pobj, unlike ordinary prep -> pobj.
        for tok in tokens:
            if tok.dep_ == 'agent':
                pobj = next((c for c in tok.children if c.dep_ == 'pobj'), None)
                if pobj is not None:
                    overrides[tok.i] = ('case', pobj.i + 1)
                    overrides[pobj.i] = ('obl', tok.head.i + 1)

        # Attach subjects of finite auxiliaries to the lexical verb.
        for tok in tokens:
            if tok.dep_ in {'nsubj', 'nsubjpass'}:
                aux = tok.head
                if (aux.pos_ == 'AUX' and aux.dep_ in {'aux', 'auxpass'}
                        and aux.head is not aux
                        and aux.head.pos_ in {'VERB', 'AUX'}):
                    overrides[tok.i] = (tok.dep_, aux.head.i + 1)

        # Recover lexical root when inverted perfect auxiliary is parsed as ROOT.
        # Require an initial negative adverb and a participle with its own subject.
        root_aux = next((t for t in tokens if t.dep_ == 'ROOT' and t.text.lower() in {'have', 'has', 'had'}), None)
        if root_aux is not None and any(
                t.dep_ == 'advmod' and t.i < root_aux.i
                and t.text.lower() in {'rarely', 'seldom', 'never', 'hardly', 'scarcely'}
                and t.head.i == root_aux.i for t in tokens):
            lexical = [t for t in root_aux.children if t.dep_ == 'ccomp'
                       and t.text.lower() not in {'been'}
                       and any(c.dep_ in {'nsubj', 'nsubjpass'} for c in t.children)]
            if len(lexical) == 1:
                verb = lexical[0]
                overrides[verb.i] = ('root', 0)
                overrides[root_aux.i] = ('aux', verb.i + 1)
                for c in root_aux.children:
                    if c.dep_ == 'advmod':
                        overrides[c.i] = ('advmod', verb.i + 1)

        # Recover main predicate after an inverted past-perfect condition.
        # The initial had + subject + participle precedes a comma and
        # a second finite clause with an independent subject.
        initial_root = next((t for t in tokens if t.dep_ == 'ROOT'), None)
        if (initial_root is not None and initial_root.text.lower() not in {'had', 'have', 'has'}
                and any(c.dep_ == 'aux' and c.text.lower() == 'had'
                        and c.i < initial_root.i for c in initial_root.children)
                and any(c.dep_ == 'nsubj' for c in initial_root.children)):
            candidates = [c for c in initial_root.children
                          if c.dep_ in {'ccomp', 'advcl'}
                          and any(x.dep_ == 'nsubj' for x in c.children)
                          and any(x.dep_ == 'aux' and x.tag_ == 'MD'
                                  for x in c.children)
                          and any(t.text == ',' and initial_root.i < t.i < c.i
                                  for t in tokens)]
            if len(candidates) == 1:
                main = candidates[0]
                overrides[main.i] = ('root', 0)
                overrides[initial_root.i] = ('advcl', main.i + 1)

        # In causative/perception SVOC, spaCy may attach the object as
        # subject of a clausal complement. Promote that noun to matrix O;
        # keep the embedded verb as a separate open complement (C).
        for tok in tokens:
            if (tok.dep_ in {'ccomp', 'xcomp'} and tok.pos_ == 'VERB'
                    and tok.tag_ in {'VB', 'VBG'}
                    and tok.head.lemma_.lower() in {
                        'make', 'let', 'have', 'see', 'watch', 'hear',
                        'feel', 'notice', 'observe'
                    }):
                subjects = [c for c in tok.children if c.dep_ == 'nsubj'
                            and c.pos_ in {'NOUN', 'PROPN', 'PRON'}]
                if len(subjects) == 1 and not any(
                        c.dep_ in {'dobj', 'obj'} for c in tok.head.children):
                    overrides[subjects[0].i] = ('obj', tok.head.i + 1)
                    overrides[tok.i] = ('xcomp', tok.head.i + 1)

        # Treat non-finite adjectival/nominal complements as object complements.
        for tok in tokens:
            if (tok.dep_ in {'ccomp', 'xcomp', 'oprd'}
                    and tok.pos_ in {'ADJ', 'NOUN', 'PROPN'}
                    and self._object_complement_verb(tok.head.lemma_)
                    and not any(c.dep_ in {'aux', 'auxpass', 'cop'} for c in tok.children)):
                overrides[tok.i] = ('oprd', tok.head.i + 1)
                for child in tok.children:
                    if child.dep_ == 'nsubj':
                        overrides[child.i] = ('obj', tok.head.i + 1)

        # Repair a narrowly identifiable initial adverbial clause mistakenly
        # chosen as ROOT. The conjunction must mark that clause, and a
        # separate finite predicate with its own subject must follow the comma.
        # Do NOT classify every 'when/if/after' as adverbial: e.g.
        # "I know when she lives here" contains a nominal complement.
        adverbial_markers = {
            'when', 'while', 'because', 'although', 'though', 'if',
            'unless', 'before', 'after', 'since', 'until', 'once',
            'whereas', 'even though', 'as soon as'
        }
        root = next((tok for tok in tokens if tok.dep_ == 'ROOT'), None)
        if root is not None and root.pos_ in {'VERB', 'AUX'}:
            marks = [c for c in root.children
                     if c.dep_ == 'mark' and c.text.lower() in adverbial_markers]
            if marks:
                comma = next((tok for tok in tokens
                              if tok.text == ',' and tok.i > root.i), None)
                if comma is not None and min(m.i for m in marks) < comma.i:
                    candidates = [
                        tok for tok in root.children
                        if tok.i > comma.i
                        and tok.dep_ in {'advcl', 'ccomp', 'conj', 'parataxis'}
                        and tok.pos_ in {'VERB', 'AUX'}
                        and any(ch.dep_ in {'nsubj', 'nsubjpass'}
                                and ch.i > comma.i for ch in tok.children)
                        and (tok.tag_ in {'VBD', 'VBP', 'VBZ', 'MD'}
                             or any(ch.dep_ in {'aux', 'auxpass'}
                                    and ch.tag_ in {'VBD', 'VBP', 'VBZ', 'MD'}
                                    for ch in tok.children))
                    ]
                    if len(candidates) == 1:
                        main = candidates[0]
                        overrides[main.i] = ('root', 0)
                        overrides[root.i] = ('advcl', main.i + 1)

        # Recover a main finite predicate that spaCy mistags as an adverb
        # inside a relative clause (e.g. "The man who smiled left.").
        # Limit this to a determiner-bearing ROOT, a single subject-relative
        # clause and a known irregular past-tense verb after that clause.
        # This is a conservative fallback, not a general POS correction.
        if (root is not None and root.dep_ == 'ROOT'
                and any(ch.dep_ == 'det' for ch in root.children)):
            relatives = [c for c in root.children if c.dep_ == 'relcl']
            irregular_past = {
                'left': 'leave', 'went': 'go', 'came': 'come',
                'ran': 'run', 'sat': 'sit', 'stood': 'stand',
                'fell': 'fall', 'spoke': 'speak', 'wrote': 'write',
                'drove': 'drive', 'slept': 'sleep', 'ate': 'eat',
            }
            if len(relatives) == 1:
                relative = relatives[0]
                has_relative_subject = any(
                    c.dep_ in {'nsubj', 'nsubjpass'}
                    and c.text.lower() in {'who', 'which', 'that'}
                    for c in relative.children
                )
                candidates = [
                    tok for tok in tokens
                    if tok.i > relative.i
                    and tok.dep_ == 'advmod'
                    and tok.head.i == relative.i
                    and (tok.text.lower() in irregular_past
                         or (tok.pos_ in {'VERB', 'AUX'}
                             and tok.tag_ in {'VBD', 'VBP', 'VBZ'}))
                ]
                if has_relative_subject and len(candidates) == 1:
                    main_verb = candidates[0]
                    overrides[main_verb.i] = ('root', 0)
                    overrides[root.i] = ('nsubj', main_verb.i + 1)
                    # Keep the relative clause attached to its noun.
                    overrides[relative.i] = ('acl:relcl', root.i + 1)

        # Repair a finite main predicate incorrectly tagged as an adjective
        # when a sentence-initial free relative clause is chosen as ROOT.
        # Require a wh-object, an embedded subject, a following predicate
        # candidate, and its own object. Do not apply to ordinary relatives.
        if (root is not None and root.dep_ == 'ROOT'
                and tokens and tokens[0].text.lower() == 'what'
                and tokens[0].head.i == root.i
                and tokens[0].dep_ in {'dobj', 'obj'}
                and any(ch.dep_ == 'nsubj' and ch.i < root.i
                        for ch in root.children)):
            main_predicates = {'surprised', 'shocked', 'amazed', 'pleased',
                               'frightened', 'impressed', 'confused', 'worried'}
            candidates = [
                tok for tok in tokens
                if tok.i > root.i and tok.text.lower() in main_predicates
                and tok.dep_ in {'amod', 'acomp'}
                and any(obj.i > tok.i and obj.dep_ in {'dobj', 'obj'}
                        and obj.head.i == root.i and tok.head.i == obj.i
                        for obj in tokens)
            ]
            if len(candidates) == 1:
                predicate = candidates[0]
                overrides[predicate.i] = ('root', 0)
                overrides[root.i] = ('csubj', predicate.i + 1)
                # Sentence-final punctuation belongs to the recovered main
                # predicate, not to the embedded nominal subject.
                for punct in tokens:
                    if (punct.dep_ == 'punct' and punct.head.i == root.i
                            and punct.i > predicate.i):
                        overrides[punct.i] = ('punct', predicate.i + 1)
                for obj in tokens:
                    if (obj.i > predicate.i and obj.dep_ in {'dobj', 'obj'}
                            and obj.head.i == root.i and predicate.head.i == obj.i):
                        overrides[obj.i] = ('obj', predicate.i + 1)

        # Recognize a narrowly identified it-cleft: the following that-clause
        # explains the focused complement, not a matrix object.
        if (root is not None and root.lemma_.lower() == 'be'
                and any(t.dep_ == 'nsubj' and t.text.lower() == 'it'
                        and t.head.i == root.i for t in tokens)
                and any(t.dep_ == 'attr' and t.head.i == root.i
                        for t in tokens)):
            focused = [t for t in tokens if t.dep_ == 'attr'
                       and t.head.i == root.i]
            for tok in tokens:
                if (len(focused) == 1 and tok.dep_ == 'ccomp'
                        and tok.head.i == root.i
                        and any(c.dep_ == 'nsubj' and c.text.lower() == 'that'
                                for c in tok.children)):
                    # Attach the cleft clause to its focus, not to matrix be.
                    # This prevents the main clause from treating it as O.
                    overrides[tok.i] = ('acl:relcl', focused[0].i + 1)

        # Passive it-clefts: the focus clause may have passive 'that' as subject.
        if (root is not None and root.lemma_.lower() == 'be'
                and any(t.dep_ == 'nsubj' and t.text.lower() == 'it'
                        and t.head.i == root.i for t in tokens)):
            focuses = [t for t in tokens if t.dep_ == 'attr' and t.head.i == root.i]
            if len(focuses) == 1:
                for tok in tokens:
                    if (tok.dep_ == 'ccomp' and tok.head.i == root.i
                            and any(c.text.lower() == 'that'
                                    and c.dep_ in {'nsubjpass', 'nsubj'}
                                    for c in tok.children)):
                        overrides[tok.i] = ('acl:relcl', focuses[0].i + 1)

        # Perception verbs sometimes receive a bare-infinitive ccomp despite
        # an already identified matrix object (watch X leave).
        for tok in tokens:
            if (tok.dep_ == 'ccomp' and tok.tag_ == 'VB'
                    and tok.head.lemma_.lower() in {'watch', 'see', 'hear', 'feel', 'notice'}
                    and any(c.dep_ == 'dobj' for c in tok.head.children)
                    and not any(c.dep_ == 'nsubj' for c in tok.children)):
                overrides[tok.i] = ('xcomp', tok.head.i + 1)

        # Absolute participial adjuncts can be misread as a detached noun.
        # Require a pre-comma nominal with its own perfect participle.
        if root is not None:
            comma = next((t for t in tokens if t.text == ',' and t.i < root.i), None)
            if comma is not None:
                absolutes = [t for t in tokens
                             if t.dep_ == 'dep' and t.head.i == root.i
                             and t.i < comma.i
                             and any(c.dep_ == 'acl' and c.i < comma.i
                                     and any(a.text.lower() == 'having'
                                             and a.dep_ == 'aux' for a in c.children)
                                     for c in t.children)]
                if len(absolutes) == 1:
                    nominal = absolutes[0]
                    participle = next(c for c in nominal.children
                                      if c.dep_ == 'acl' and c.i < comma.i)
                    overrides[participle.i] = ('advcl', root.i + 1)
                    overrides[nominal.i] = ('nsubj', participle.i + 1)

        # Normalize postverbal subjects in locative inversion.
        # Require an initial locative PP and a finite intransitive predicate.
        if root is not None and root.lemma_.lower() in {'stand', 'sit', 'lie', 'remain', 'appear', 'come', 'go'}:
            locative = any(t.dep_ == 'prep' and t.i < root.i and t.head.i == root.i for t in tokens)
            if locative and not any(t.dep_ in {'nsubj', 'nsubjpass'} and t.head.i == root.i for t in tokens):
                nominal = [t for t in tokens if t.head.i == root.i and t.i > root.i
                           and t.dep_ in {'dobj', 'attr'} and t.pos_ in {'NOUN', 'PROPN', 'PRON'}]
                if len(nominal) == 1:
                    overrides[nominal[0].i] = ('nsubj', root.i + 1)

        # spaCy occasionally labels an object-predicative adjective as
        # advmod (e.g. 'painted the door red'). Keep it distinct from adverbs.
        for tok in tokens:
            if (tok.dep_ == 'advmod' and tok.pos_ == 'ADJ'
                    and self._object_complement_verb(tok.head.lemma_)
                    and any(c.dep_ in {'dobj', 'obj'} for c in tok.head.children)):
                overrides[tok.i] = ('oprd', tok.head.i + 1)

        dep_map = {
            'ROOT': 'root',
            'nsubjpass': 'nsubj:pass',
            'csubjpass': 'csubj:pass',
            'auxpass': 'aux:pass',
            'dobj': 'obj',
            'dative': 'iobj',
            'relcl': 'acl:relcl',
            'poss': 'nmod:poss',
            'prt': 'compound:prt',
            'npadvmod': 'npmod',
        }

        words = []
        for tok in tokens:
            dep = dep_map.get(tok.dep_, tok.dep_)
            head = 0 if tok.dep_ == 'ROOT' else tok.head.i + 1
            if tok.i in overrides:
                dep, head = overrides[tok.i]
            words.append(Word(
                id=tok.i + 1,
                text=tok.text,
                lemma=tok.lemma_,
                upos=tok.pos_,
                xpos=tok.tag_,
                head=head,
                deprel=dep,
            ))
        return Sentence(text=span.text, words=words)

    def analyze(self, text: str) -> dict:
        doc = self.nlp(text)
        sentences = [self._convert_sentence(s) for s in doc.sents]
        return {
            'schema_version': '1.0',
            'engine': 'spacy-en_core_web_sm',
            'text': text,
            'sentences': [self._sentence(s, i+1) for i, s in enumerate(sentences)]
        }

    def _sentence(self, sent, idx: int) -> dict:
        ids = IdFactory(idx, {})
        words = list(sent.words)
        by_id = {w.id: w for w in words}
        children: Dict[int, List] = {w.id: [] for w in words}
        for w in words:
            if w.head in children:
                children[w.head].append(w)
        roots = [w for w in words if w.head == 0]
        root = roots[0] if roots else words[0]
        clause_heads = [w for w in words if w.head == 0 or
                        (w.deprel in CLAUSE_RELS and not
                         (w.deprel == 'xcomp' and w.upos in {'ADJ', 'NOUN', 'PROPN'}
                          and w.head in by_id and
                          (self._linking_verb(by_id[w.head].lemma)
                           or self._object_complement_verb(by_id[w.head].lemma))))]
        clause_heads = sorted({w.id:w for w in clause_heads}.values(), key=lambda w:w.id)
        clause_map = {w.id: ids.make('cl') for w in clause_heads}
        relations, tags, warnings = [], set(), []
        clauses = []
        for head in clause_heads:
            clauses.append(self._clause(head, root, by_id, children, clause_heads, clause_map, ids, relations, tags, warnings))
        self._global_relations(words, children, ids, relations, tags)
        tokens = [{
            'id': ids.make('tok'), 'index': w.id, 'text': w.text, 'lemma': w.lemma,
            'upos': w.upos, 'xpos': w.xpos, 'head': w.head, 'deprel': w.deprel
        } for w in words]
        return {
            'id': f'SENT-{idx:03d}', 'text': sent.text, 'tokens': tokens,
            'root_token': root.id, 'clauses': clauses, 'relations': relations,
            'tags': sorted(tags), 'warnings': sorted(set(warnings))
        }

    def _clause(self, head, sentence_root, by_id, children, clause_heads, clause_map, ids, relations, tags, warnings):
        cid = clause_map[head.id]
        ctype = self._clause_type(head, sentence_root, by_id, children)
        if head.deprel == 'acl:relcl': tags.add('relative_clause')
        if head.deprel in {'ccomp','xcomp'}: tags.add('complement_clause')
        if head.deprel == 'advcl': tags.add('adverbial_clause')
        if any(c.deprel == 'cc' for c in children.get(head.id, [])) or head.deprel == 'conj': tags.add('coordination')
        if any(c.deprel == 'neg' or c.lemma == 'not' for c in children.get(head.id, [])): tags.add('negation')
        if any(c.deprel == 'expl' and c.lemma == 'there' for c in children.get(head.id, [])): tags.add('existential_there')

        excluded_heads = {w.id for w in clause_heads if w.id != head.id and self._belongs_under(w, head, by_id)}
        clause_token_ids = sorted(self._subtree_ids(head.id, children) - set().union(*(self._subtree_ids(x, children) for x in excluded_heads)) if excluded_heads else self._subtree_ids(head.id, children))

        core = {'S': [], 'V': [], 'O': [], 'C': [], 'M': []}
        direct = children.get(head.id, [])
        for w in direct:
            if w.deprel in SUBJECT_RELS and not w.deprel.startswith('csubj'):
                core['S'].append(self._element(w, 'S', children, ids))
            elif w.deprel in OBJECT_RELS:
                core['O'].append(self._element(w, 'O', children, ids))
            elif (w.deprel in MOD_RELS and w.deprel not in CLAUSE_RELS) or (w.deprel == 'neg' and w.text.lower() not in {'not', "n't"}):
                core['M'].append(self._element(w, 'M', children, ids))
        # School-grammar convention for existential there:
        # there=M (existential marker), postverbal nominal=S, be=V.
        # Postnominal prepositional modifiers are separate M elements.
        existential = [w for w in direct if w.deprel == 'expl'
                       and w.text.lower() == 'there']
        if existential and head.lemma.lower() == 'be':
            postverbal = [w for w in direct
                          if w.deprel in {'attr', 'nsubj'}
                          and w.id > head.id
                          and w.upos in {'NOUN', 'PROPN', 'PRON'}]
            if len(existential) == 1 and len(postverbal) == 1:
                nominal = postverbal[0]
                core['S'] = [e for e in core['S']
                             if e['head_token'] != nominal.id]
                core['S'].append(self._element(nominal, 'S', children, ids))
                marker = self._element(existential[0], 'M', children, ids)
                marker['subtype'] = 'existential_marker'
                core['M'].append(marker)
                for mod in children.get(nominal.id, []):
                    if (mod.deprel == 'obl'
                            and any(ch.deprel == 'case'
                                    for ch in children.get(mod.id, []))):
                        pp_ids = self._subtree_ids(mod.id, children)
                        pp = {'id': ids.make('m'), 'role': 'M',
                              'text': ' '.join(by_id[i].text for i in sorted(pp_ids)),
                              'token_ids': sorted(pp_ids), 'head_token': mod.id,
                              'modifies_token': nominal.id}
                        core['M'].append(pp)
                        relations.append({'id': ids.make('rel'),
                                          'type': 'modifies',
                                          'source_token': mod.id,
                                          'target_token': nominal.id})

        # Adverbial degree modifiers of an adjective complement are M,
        # even when the adjective itself is classified as C.
        for adj in direct:
            if adj.deprel in {'acomp', 'attr', 'oprd'} and adj.upos == 'ADJ':
                for mod in children.get(adj.id, []):
                    if mod.deprel == 'advmod' and mod.text.lower() == 'how':
                        if not any(e['head_token'] == mod.id for e in core['M']):
                            core['M'].append(self._element(mod, 'M', children, ids))

        # Comparative clauses often attach to the comparative adverb,
        # rather than directly to the main verb.
        for modifier in direct:
            if modifier.deprel == 'advmod':
                for subordinate in children.get(modifier.id, []):
                    if (subordinate.deprel == 'advcl'
                            and any(marker.deprel == 'mark'
                                    and marker.text.lower() == 'than'
                                    for marker in children.get(subordinate.id, []))):
                        core['M'].append({
                            'id': ids.make('m'), 'role': 'M',
                            'text': self._span_text(subordinate, children),
                            'token_ids': sorted(self._subtree_ids(subordinate.id, children)),
                            'head_token': subordinate.id,
                            'modifies_token': modifier.id,
                        })

        # Some spaCy parses attach the subject to an auxiliary (was)
        # rather than to its lexical verb (cooking).
        for aux in direct:
            if aux.deprel in {'aux', 'aux:pass'}:
                for subject in children.get(aux.id, []):
                    if subject.deprel in SUBJECT_RELS and not any(
                        e['head_token'] == subject.id for e in core['S']
                    ):
                        core['S'].append(self._element(subject, 'S', children, ids))

        verb_words = [head] + [w for w in direct if w.deprel in AUX_RELS and (w.deprel != 'neg' or w.text.lower() in {'not', "n't"})]
        verb_words = sorted({w.id:w for w in verb_words}.values(), key=lambda w:w.id)
        core['V'].append({'id': ids.make('v'), 'role':'V', 'text':' '.join(w.text for w in verb_words), 'token_ids':[w.id for w in verb_words], 'head_token':head.id})

        complements = self._complements(head, direct, children, ids)
        if existential and head.lemma.lower() == 'be' and len(postverbal) == 1:
            complements = [comp for comp in complements
                           if comp['head_token'] != postverbal[0].id]
        core['C'].extend(complements)
        for comp in complements:
            comp['complement_of'] = 'O' if core['O'] and self._object_complement_verb(head.lemma) else 'S'
            target = core[comp['complement_of']][-1]['id'] if core[comp['complement_of']] else None
            if target:
                relations.append({'id':ids.make('rel'),'type':'complements','source':comp['id'],'target':target})

        child_clause_refs = []
        for ch in clause_heads:
            if ch.id == head.id or ch.head != head.id: continue
            role = ('M' if ch.deprel == 'advcl' else 'S' if ch.deprel.startswith('csubj') else 'O' if ch.deprel == 'xcomp' and (head.lemma or '').lower() in {'decide'} and any(t.text.lower() == 'to' and t.deprel in {'aux', 'mark'} for t in children.get(ch.id, [])) else 'C' if ch.deprel == 'xcomp' else 'O')
            ref = {'id':ids.make(role.lower()), 'role':role, 'text':self._span_text(ch, children), 'token_ids':sorted(self._subtree_ids(ch.id, children)), 'head_token':ch.id, 'clause_ref':clause_map[ch.id]}
            if role == 'C' and ch.deprel == 'xcomp' and ch.xpos == 'VB':
                adjuncts = [w for w in children.get(ch.id, [])
                            if w.deprel in {'advmod', 'obl', 'npmod'}]
                if adjuncts:
                    exclude = set().union(*(self._subtree_ids(w.id, children) for w in adjuncts))
                    keep = [i for i in ref['token_ids'] if i not in exclude]
                    ref['full_text'] = ref['text']
                    ref['text'] = ' '.join(by_id[i].text for i in keep)
                    ref['token_ids'] = keep
                    ref['attached_modifiers'] = [self._span_text(w, children) for w in adjuncts]
            if role == 'M' and ch.deprel == 'advcl':
                keep = [i for i in ref['token_ids'] if by_id[i].deprel != 'punct']
                ref['token_ids'] = keep
                ref['text'] = ' '.join(by_id[i].text for i in keep)
            formal_it = next((item for item in core['S'] if item['text'].lower() == 'it'), None)
            extraposed = (formal_it is not None and ch.deprel == 'ccomp'
                          and ((head.lemma or '').lower() == 'follow'
                               or ((head.lemma or '').lower() in {'remain', 'be', 'seem'}
                                   and bool(core['C'])))
                          and any(t.text.lower() in {'that', 'whether'} and t.deprel == 'mark'
                                  for t in children.get(ch.id, [])))
            if extraposed:
                relations.append({'id': ids.make('rel'), 'type': 'extraposed_subject',
                                  'source_clause_head': ch.id,
                                  'target_token': formal_it['head_token']})
                tags.add('extraposed_subject')
            else:
                core[role].append(ref)
            child_clause_refs.append(clause_map[ch.id])

        # A preposed degree adverb (How beautiful...) modifies C, not part of C.\n        for comp in core['C']:\n            for mod in children.get(comp['head_token'], []):\n                if mod.deprel == 'advmod' and mod.text.lower() == 'how':\n                    core['M'].append(self._element(mod, 'M', children, ids))\n\n        # Keep compatibility with UD-style copular input if encountered.
        copulas = [w for w in direct if w.deprel == 'cop']
        if copulas:
            core['V'] = [{'id':ids.make('v'),'role':'V','text':' '.join(w.text for w in sorted(copulas, key=lambda x:x.id)), 'token_ids':[w.id for w in sorted(copulas,key=lambda x:x.id)], 'head_token':copulas[0].id}]
            pred = {'id':ids.make('c'),'role':'C','text':self._phrase_text(head, children),'token_ids':sorted(self._phrase_ids(head, children)), 'head_token':head.id, 'complement_of':'S'}
            core['C'].insert(0, pred)
            if core['S']:
                relations.append({'id':ids.make('rel'),'type':'complements','source':pred['id'],'target':core['S'][0]['id']})

        if not core['S'] and ctype == 'main' and head.upos in {'VERB','AUX'}:
            if head.xpos == 'VB': tags.add('imperative_candidate')
            else: warnings.append(f'{cid}: 主語を明確に特定できませんでした。')

        phrases = self._phrases_for_clause(clause_token_ids, by_id, children, ids)
        return {
            'id':cid, 'type':ctype, 'head_token':head.id,
            'text':' '.join(by_id[i].text for i in clause_token_ids if i in by_id),
            'token_ids':clause_token_ids, 'core':core, 'phrases':phrases,
            'child_clauses':child_clause_refs,
            'confidence':'medium' if warnings else 'high'
        }

    def _clause_type(self, head, root, by_id, children):
        if head.id == root.id: return 'main'
        if head.deprel == 'acl:relcl': return 'relative'
        if head.deprel == 'advcl': return 'adverbial'
        if head.deprel in {'csubj','csubj:pass'}: return 'nominal-subject'
        if head.deprel == 'ccomp': return 'nominal-complement'
        if head.deprel == 'xcomp': return 'open-complement'
        if head.deprel == 'parataxis': return 'parataxis'
        return 'embedded'

    def _complements(self, head, direct, children, ids):
        out=[]
        if self._linking_verb(head.lemma):
            for w in direct:
                if ((w.deprel in {'xcomp','obl','attr','acomp'} and w.upos in {'ADJ','NOUN','PROPN'})
                        or ((head.lemma or '').lower() == 'be' and w.deprel in {'attr','acomp','oprd'})):
                    out.append(self._element(w,'C',children,ids))
        if self._object_complement_verb(head.lemma):
            for w in direct:
                if ((w.deprel in {'xcomp','oprd'} and w.upos in {'ADJ','NOUN','PROPN'})
                        or (w.deprel == 'oprd' and w.upos == 'VERB')):
                    out.append(self._element(w,'C',children,ids))
        return out

    def _element(self, w, role, children, ids):
        tids = sorted(self._phrase_ids(w, children))
        return {'id':ids.make(role.lower()), 'role':role, 'text':self._phrase_text(w,children), 'token_ids':tids, 'head_token':w.id}

    def _phrase_ids(self, w, children):
        allowed = set()
        def walk(node):
            allowed.add(node.id)
            for c in children.get(node.id, []):
                if (c.deprel in NP_EXPAND or c.deprel in {'fixed','compound:prt','case'} or (w.deprel == 'obl' and c.deprel == 'obl' and any(x.deprel == 'case' for x in children.get(c.id, [])))):
                    walk(c)
        walk(w)
        return allowed

    def _phrase_text(self, w, children):
        nodes=[]
        ids=self._phrase_ids(w,children)
        all_nodes={x.id:x for vals in children.values() for x in vals}
        all_nodes[w.id]=w
        for i in sorted(ids):
            if i in all_nodes: nodes.append(all_nodes[i].text)
        return ' '.join(nodes)

    def _phrases_for_clause(self, token_ids, by_id, children, ids):
        phrases=[]
        for i in token_ids:
            w=by_id[i]
            ptype=None
            if w.upos in {'NOUN','PROPN','PRON'}: ptype='NP'
            elif w.deprel == 'obl' and any(c.deprel=='case' for c in children.get(w.id,[])): ptype='PP'
            elif w.upos=='VERB' and any(c.lemma=='to' and c.deprel=='mark' for c in children.get(w.id,[])): ptype='Infinitive'
            elif w.upos=='VERB' and w.xpos in {'VBG','VBN'}: ptype='Participle/Gerund'
            if ptype:
                phrases.append({'id':ids.make('ph'),'type':ptype,'head_token':w.id,'text':self._phrase_text(w,children),'token_ids':sorted(self._phrase_ids(w,children))})
        return phrases

    def _global_relations(self, words, children, ids, relations, tags):
        for w in words:
            if w.deprel in {'amod','advmod','nmod','acl','acl:relcl','appos'} and w.head:
                relations.append({'id':ids.make('rel'),'type':'modifies','source_token':w.id,'target_token':w.head})
            if w.deprel == 'conj' and w.head:
                relations.append({'id':ids.make('rel'),'type':'coordinates','source_token':w.id,'target_token':w.head})
                tags.add('coordination')
            if w.deprel == 'acl:relcl':
                rels=[c for c in children.get(w.id,[]) if c.lemma and c.lemma.lower() in REL_WORDS]
                if rels:
                    for r in rels:
                        relations.append({'id':ids.make('rel'),'type':'refers_to','source_token':r.id,'target_token':w.head})
                else:
                    tags.add('relative_pronoun_omission_candidate')
                    relations.append({'id':ids.make('rel'),'type':'omitted_element','source_clause_head':w.id,'target_token':w.head,'note':'relative element may be omitted'})
            if w.lemma in {'more','less','than','as'}: tags.add('comparison_candidate')
        for h in words:
            ch=children.get(h.id,[])
            subs=[x for x in ch if x.deprel in SUBJECT_RELS]
            aux=[x for x in ch if x.deprel.startswith('aux')]
            if subs and aux and min(x.id for x in aux) < min(x.id for x in subs): tags.add('inversion_candidate')

    def _subtree_ids(self, root_id, children) -> Set[int]:
        out=set()
        def walk(i):
            if i in out:return
            out.add(i)
            for c in children.get(i,[]): walk(c.id)
        walk(root_id); return out

    def _belongs_under(self, node, ancestor, by_id):
        cur=node
        seen=set()
        while cur.head and cur.head not in seen:
            if cur.head == ancestor.id:return True
            seen.add(cur.head)
            cur=by_id.get(cur.head)
            if cur is None:return False
        return False

    def _span_text(self, w, children):
        ids=sorted(self._subtree_ids(w.id,children))
        all_nodes={x.id:x for vals in children.values() for x in vals}; all_nodes[w.id]=w
        return ' '.join(all_nodes[i].text for i in ids if i in all_nodes)

    @staticmethod
    def _linking_verb(lemma):
        return (lemma or '').lower() in {'be','become','seem','appear','remain','feel','look','sound','smell','taste','grow','turn','prove'}

    @staticmethod
    def _object_complement_verb(lemma):
        return (lemma or '').lower() in {'find','make','keep','consider','call','name','elect','appoint','paint','drive','leave'}
