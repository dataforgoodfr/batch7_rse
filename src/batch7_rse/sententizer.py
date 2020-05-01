import spacy
from spacy.tokens import Span
import pandas as pd
import numpy as np
import multiprocessing as mp
MIN_NB_OF_WORDS = 3


def get_nb_words(doc):
    """ Count numer of tokens in spacy Doc, ignoring NUM and ADP (e.g. for, at...) and not counting % as noun. """
    return len([token for token in doc if (token.pos_ in ["NOUN","PROPN","VERB"]) and (token.text!="%")])


def exception_to_split(token):
    """Identify usage of cf. to forbid splitting."""
    if 'cf' in token.nbor(-2).text and token.nbor(-1).text == ".":
        return True
    return False


def custom_sentence_boundaries(doc):
    """ Implement exception to split."""
    for i, token in enumerate(doc[2:]):
        if exception_to_split(token):
            token.is_sent_start = False
    return doc


def load_nlp_sententizer_object():
    """ Load french mspacy model, customize it, add custom nb_words attributes to Span."""
    Span.set_extension("nb_words", setter=get_nb_words, getter=get_nb_words, force=True)
    if not spacy.util.is_package("fr_core_news_sm"):
        print("Downloading fr_core_news_sm spacy model...")
        spacy.cli.download('fr_core_news_sm')
        print("done.")
    nlp = spacy.load('fr_core_news_sm')
    nlp.add_pipe(custom_sentence_boundaries, before = "parser")  # add exception to sententizer
    nlp.add_pipe(nlp.create_pipe('sentencizer'))  # to add default sentencizer, AFTER custom rule
    return nlp


def sententize_df(df):
    nlp = load_nlp_sententizer_object()
    df["paragraph_sentences"] = df["paragraph"].apply(
        lambda x: [sent.text for sent in nlp(x).sents if sent._.nb_words > MIN_NB_OF_WORDS]
    ).values
    df = df[df["paragraph_sentences"].apply(lambda x: len(x) > 0)]  # keep if there was >0 valid sentences
    return df

# TODO: maybe use this in pdf_parser as well ?
def parallelize_dataframe_apply(df, func):
    n_cores = mp.cpu_count()-1 or 1   # use all except one if more than one available
    df_split = np.array_split(df, n_cores)
    print("Parallel sententization with {} cores".format(n_cores))
    pool = mp.Pool(n_cores)
    df = pd.concat(pool.map(func, df_split))
    pool.close()
    pool.join()
    return df


# TODO: optimize with parallelism or direct writing to sql database
# TODO: parallelize the index as well ?
# Takes > 20 sec for 4 (large) dpefs (Energéticien) so not really scalable...
def run_sententizer(input_filename="../../data/processed/DPEFs/dpef_paragraphs.csv",
                    output_filename="../../data/processed/DPEFs/dpef_paragraphs_sentences.csv"):
    """
    Transform paragrph level text to sentence level text, keeping only sentences with more than N words
    :param input_filename: relative path to input paragraph level csv (; separaed)
    :param output_filename: relative path to output sentence level csv (; separaed)
    :return:
    """
    print("Reading paragraph level data.")
    df = pd.read_csv(input_filename, sep=";")
    df = df[df.paragraph.notna()] # sanity check
    df = parallelize_dataframe_apply(df, sententize_df)
    # convert to 1 row / sentence format
    print("Get sentence level structure")
    df = (df
           .set_index(df.columns[:-1].values.tolist())['paragraph_sentences']  # all except last colname as index
           .apply(pd.Series)
           .stack()
           .reset_index()
           .drop('level_{}'.format(len(df.columns) - 1), axis=1)
           .rename(columns={0: 'sentence'}))
    # save
    df.to_csv(output_filename, sep=";")
    return df
