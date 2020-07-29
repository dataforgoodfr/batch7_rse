import pandas as pd
import spacy
import rse_watch.spacy_filters as sf

# force = True because this function is called twice.
spacy.tokens.Doc.set_extension("scoring_weight", default=-1, force=True)  # weight based on BM25 weights




def get_nb_words(doc):
    """ Count numer of tokens in spacy Doc, ignoring NUM and ADP (e.g. for, at...) and not counting % as noun. """
    return len([token for token in doc if (token.pos_ not in IGNORED_POS) and (token.text != "%")])


spacy.tokens.Span.set_extension("nb_words", setter=get_nb_words, getter=get_nb_words, force=True)


# Global parameters
# Approach: learn that they are common (i.e. keep for scorer), but ignore them in final vectorization.
# Ref: https://spacy.io/api/annotation
IGNORED_POS = ["ADP",  # in, to, during
               "AUX",  #is, has (done), will (do), should (do)
               "CONJ",  # and, or, but
               "CCONJ",  # and, or, but
               "DET",  # a, an the
               "INTJ",  # psst, ouch, bravo, hello
               "PART",  # 's, not'
               "PRON",  # I, you, he, she, myself, themselves, somebody
               "PUNCT",  # punctuation
               "SCONJ",  # if, while, that
               "SYM",  # symbols
               "X",  # others
               "SPACE"]

def exception_to_split(token):
    # Identify usage of cf. to forbid splitting
    if 'cf' in token.nbor(-2).text and token.nbor(-1).text == ".":
        return True
    # do not split if sentence ends with an apostrophe
    if token.nbor(-1).text == "'":
        return True
    return False


def custom_sentence_boundaries(doc):
    """ Implement exception to split."""
    for i, token in enumerate(doc[2:]):
        if exception_to_split(token):
            token.is_sent_start = False
    return doc

# TODO: should here be not in IGNORED_POS or is this done later ?
def get_span_metadata(sent):
    text = sent.text
    text_tokens = "|".join([token.text.lower() for token in sent if token.pos_ not in IGNORED_POS])
    dates = sf.isDate(sent)
    return pd.Series([text, text_tokens, dates])


def load_nlp_sententizer_object(config):
    """ Load french sm (small) spacy model, customize it, add custom nb_words attributes to Span."""
    if not spacy.util.is_package("fr_core_news_sm"):
        print("Downloading fr_core_news_sm spacy model...")
        spacy.cli.download('fr_core_news_sm')
        print("done.")
    nlp = spacy.load("fr_core_news_sm")
    nlp.remove_pipe("parser")  # elsewise splits sentences on ' and some uppercase...
    nlp.add_pipe(custom_sentence_boundaries)  # add exception to sententizer: apostroph, cf., ...
    nlp.add_pipe(nlp.create_pipe('sentencizer'))  # to add default sentencizer, AFTER custom rule
    return nlp


def get_sentence_dataframe_from_paragraph_dataframe(df_par, config):
    nlp = load_nlp_sententizer_object(config)
    df_sent = df_par
    df_sent["paragraph_sentences"] = df_sent["paragraph"].apply(
        lambda x: [sent for sent in nlp(x).sents if sent._.nb_words >= config.MIN_NB_OF_WORDS]
    ).values
    df_sent = df_sent[
        df_sent["paragraph_sentences"].apply(lambda x: len(x) > 0)]  # keep if there was >0 valid sentences
    df_sent = (df_sent
               .set_index(df_sent.columns[:-1].values.tolist())[
                   'paragraph_sentences']  # all except last colname as index
               .apply(pd.Series)
               .stack()
               .reset_index()
               .drop('level_{}'.format(len(df_sent.columns) - 1), axis=1)
               .rename(columns={0: 'sentence'}))
    df_sent[["sentence",
             "sentence_tokens",
             "dates"]] = df_sent[["sentence"]]. \
        apply(lambda row: get_span_metadata(row["sentence"]),
              axis=1,
              result_type="expand")

    return df_sent
