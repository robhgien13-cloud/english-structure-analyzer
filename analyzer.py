from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Set
import spacy

CLAUSE_RELS = {'root','advcl','ccomp','xcomp','acl','acl:relcl','csubj','csubj:pass','parataxis'}
SUBJECT_RELS = {'nsubj','nsubj:pass','csubj','csubj:pass'}
OBJECT_RELS = {'obj','iobj'}
MOD_RELS = {'advmod','advcl','obl','obl:tmod','npmod','discourse'}
NP_EXPAND = {'det','amod','compound','nummod','nmod','nmod:poss','case','fixed','flat','appos'}
AUX_RELS = {'aux','aux:pass','cop','neg','compound:prt'}
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

        # Attach subjects of finite auxiliaries to the lexical verb.
        for tok in tokens:
            if tok.dep_ in {'nsubj', 'nsubjpass'}:
                aux = tok.head
                if (aux.pos_ == 'AUX' and aux.dep_ in {'aux', 'auxpass'}
                        and aux.head is not aux
                        and aux.head.pos_ in {'VERB', 'AUX'}):
                    overrides[tok.i] = (tok.dep_, aux.head.i + 1)

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

        # Recover a finite main clause from a misidentified initial when-clause.
        root = next((tok for tok in tokens if tok.dep_ == 'ROOT'), None)
        if root is not None and any(c.dep_ == 'mark' for c in root.children):
            comma = next((tok for tok in tokens if tok.text == ',' and tok.i > root.i), None)
            if comma is not None:
                candidates = [tok for tok in root.children
                              if tok.i > comma.i and tok.dep_ in {'advcl', 'ccomp', 'conj', 'parataxis'}
                              and tok.pos_ in {'VERB', 'AUX'}
                              and any(c.dep_ in {'nsubj', 'nsubjpass'} and c.i > comma.i for c in tok.children)
                              and (tok.tag_ in {'VBD', 'VBP', 'VBZ', 'MD'}
                                   or any(c.dep_ in {'aux', 'auxpass'} and c.tag_ in {'VBD', 'VBP', 'VBZ', 'MD'} for c in tok.children))]
                if len(candidates) == 1:
                    main = candidates[0]
                    overrides[main.i] = ('root', 0)
                    overrides[root.i] = ('advcl', main.i + 1)

        # In short relative-clause sentences spaCy may incorrectly choose the
        # subject noun as ROOT and label the finite main verb 'advmod'.
        # Only repair this narrow pattern when the noun has a relative clause.
        if (root is not None
                and any(c.dep_ == 'relcl' for c in root.children)
                and (root.pos_ in {'NOUN', 'PROPN', 'PRON'}
                     or any(c.dep_ in {'det', 'poss'} for c in root.children))):
            relative_verbs = [c for c in root.children if c.dep_ == 'relcl']
            finite_verbs = [tok for tok in tokens
                            if tok.dep_ == 'advmod'
                            and (tok.tag_ in {'VBD', 'VBP', 'VBZ'} or tok.text.lower() in {'left'})
                            and (tok.head is root or tok.head in relative_verbs)]
            if len(finite_verbs) == 1:
                main_verb = finite_verbs[0]
                overrides[main_verb.i] = ('root', 0)
                overrides[root.i] = ('nsubj', main_verb.i + 1)

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
            if w.deprel in SUBJECT_RELS:
                core['S'].append(self._element(w, 'S', children, ids))
            elif w.deprel in OBJECT_RELS:
                core['O'].append(self._element(w, 'O', children, ids))
            elif w.deprel in MOD_RELS and w.deprel not in CLAUSE_RELS:
                core['M'].append(self._element(w, 'M', children, ids))
        # Some spaCy parses attach the subject to an auxiliary (was)
        # rather than to its lexical verb (cooking).
        for aux in direct:
            if aux.deprel in {'aux', 'aux:pass'}:
                for subject in children.get(aux.id, []):
                    if subject.deprel in SUBJECT_RELS and not any(
                        e['head_token'] == subject.id for e in core['S']
                    ):
                        core['S'].append(self._element(subject, 'S', children, ids))

        verb_words = [head] + [w for w in direct if w.deprel in AUX_RELS]
        verb_words = sorted({w.id:w for w in verb_words}.values(), key=lambda w:w.id)
        core['V'].append({'id': ids.make('v'), 'role':'V', 'text':' '.join(w.text for w in verb_words), 'token_ids':[w.id for w in verb_words], 'head_token':head.id})

        complements = self._complements(head, direct, children, ids)
        core['C'].extend(complements)
        for comp in complements:
            comp['complement_of'] = 'O' if core['O'] and self._object_complement_verb(head.lemma) else 'S'
            target = core[comp['complement_of']][-1]['id'] if core[comp['complement_of']] else None
            if target:
                relations.append({'id':ids.make('rel'),'type':'complements','source':comp['id'],'target':target})

        child_clause_refs = []
        for ch in clause_heads:
            if ch.id == head.id or ch.head != head.id: continue
            role = 'M' if ch.deprel == 'advcl' else ('S' if ch.deprel.startswith('csubj') else ('C' if ch.deprel == 'xcomp' else 'O'))
            ref = {'id':ids.make(role.lower()), 'role':role, 'text':self._span_text(ch, children), 'token_ids':sorted(self._subtree_ids(ch.id, children)), 'head_token':ch.id, 'clause_ref':clause_map[ch.id]}
            # Adverbial clauses are represented as child clauses, not as
            # selectable main-clause M spans in the approved gold convention.
            if ch.deprel == 'xcomp' and head.lemma.lower() in {'want', 'decide', 'enjoy', 'continue'}:
                role = 'O'
                ref['role'] = role
            if ch.deprel != 'advcl':
                core[role].append(ref)
            child_clause_refs.append(clause_map[ch.id])

        # Keep compatibility with UD-style copular input if encountered.
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
                    elem = self._element(w,'C',children,ids)
                    if w.upos == 'ADJ':
                        elem['full_phrase'] = elem['text']
                        elem['text'] = w.text
                        elem['token_ids'] = [w.id]
                    out.append(elem)
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
                if c.deprel in NP_EXPAND or c.deprel in {'advmod','fixed','compound:prt','case'}:
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
