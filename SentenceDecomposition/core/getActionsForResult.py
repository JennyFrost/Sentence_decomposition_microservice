from auxiliary_functions import *
from VerbTypeChecker import VerbTypeChecker


def getActionsForResult(doc: spacy.tokens.doc.Doc,
                       token: spacy.tokens.token.Token) -> List[Tuple]:
    checker = VerbTypeChecker(doc)
    action_phrases = []
    verb = ''
    link = ''
    if isinstance(token, list):
        token_ = doc[token[-1]]
        kw_span = doc[token[0]:token[1] + 1]
        main_tok = token_
        # if all(map(lambda x: x in token_.subtree, kw_span)):
        #     main_tok = token_
        if kw_span[0] == token_.head:
            main_tok = kw_span[0]
        elif kw_span[-1] != token_ and kw_span[-1] == token_.head and kw_span[-1] == kw_span[0].head:
            main_tok = kw_span[-1]
    else:
        main_tok = token
        kw_span = doc[token.i:token.i + 1]

    if main_tok.pos_ != 'VERB':
        cj = ConjunctsHandler(doc)
        main_tok = cj.get_main_token(main_tok, kw_span)

    if main_tok.head.lemma_ == 'include':
        main_tok = main_tok.head
        if main_tok.dep_ == 'ROOT':
            action_phrases = []
    ing_ed = bool(re.search(r'(ing\b|ed\b)', main_tok.text))
    if main_tok.head.text in ['to', 'for']:
        link = main_tok.head
        if main_tok.head.head.pos_ in ('VERB', 'AUX'):
            verb = main_tok.head.head
    if main_tok.i > 0:
        if doc[main_tok.i - 1].text in ['to', 'for'] or (
                doc[main_tok.i - 1].pos_ == 'NOUN' and ing_ed):
            link = doc[main_tok.i - 1]
            if doc[main_tok.i - 1].head.pos_ in ('VERB', 'AUX'):
                verb = doc[main_tok.i - 1].head
    if main_tok.i > 1:
        if doc[main_tok.i - 2].pos_ == 'NOUN' and doc[main_tok.i - 1].text == ',' and ing_ed:
            link = doc[main_tok.i - 2]
            if doc[main_tok.i - 2].head.pos_ in ('VERB', 'AUX'):
                verb = doc[main_tok.i - 2].head
    nearest_verb = get_nearest_verb(doc, main_tok, kw_span)
    if (main_tok.head.pos_ in ('VERB', 'AUX')
        and main_tok.dep_ not in ('conj','appos','ROOT')
        and main_tok.head.text not in verbs_stoplist
        and not (main_tok.head.pos_=='AUX'
        and main_tok.head.i == main_tok.i-1)):
        verb = main_tok.head
    elif nearest_verb and nearest_verb.text not in verbs_stoplist:
        verb = nearest_verb
    if verb:
        p = get_prep(verb)
        prep = p if p else get_prep_2(doc, p, kw_span)
        main_verb, all_verbs = get_all_verbs(doc, verb)
        if main_verb.i > 0:
            if doc[main_verb.i - 1].text in ['to', 'for']:
                link = doc[main_verb.i-1]
        if main_tok.i > 1:
            if (doc[main_tok.i - 2].pos_ == 'NOUN'
                    and doc[main_tok.i - 1].text == ','
                    and ing_ed):
                link = doc[main_tok.i-2]
        verbs_text = get_verbs_text(doc, all_verbs, main_tok)
        if main_verb.lemma_ in verbs_with_ccomps:
            ccomps = get_ccomps(doc, main_verb)
            if ccomps and main_tok not in ccomps[0]:
                all_verbs, verbs_text = ccomps
        verb = all_verbs[-1]
        if verb.tag_ == 'VBZ' and list(filter(lambda x: x.text == 'it' and x.dep_ == 'nsubj', verb.children)):
            action_phrases = []
        if (checker.isResultVerb(main_verb)
            or (verb.tag_ == 'VBD'
            and main_verb.dep_ == 'amod'
            and (doc[main_verb.i - 1].pos_ == 'ADP'
            or (main_verb.head.pos_ == 'VERB'
            and main_verb.dep_ not in ('ROOT', 'conj'))))):
            other_result_tuple = get_other_result_tuple(doc, verb, main_verb, all_verbs, prep, kw_span)
            if other_result_tuple:
                action_phrases = other_result_tuple
            else:
                action_phrases = get_verb_tuples(doc, verb, all_verbs, verbs_text, prep=prep, link=link)
        else:
            action_phrases = get_verb_tuples(doc, verb, all_verbs, verbs_text, prep=prep, link=link)

    return action_phrases
