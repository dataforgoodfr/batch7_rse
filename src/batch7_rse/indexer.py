# general imports
import pandas as pd
import numpy as np
import spacy
import pickle

# local import
from scoring import Scoring
# TODO: use a conf file to have unique file paths

# Approach: learn that they are common (i.e. keep for scorer), but ignore them in final vectorization.
IGNORED_POS = ['PRON', 'AUX', 'DET', "PUNCT"]


def initialize_scoring(input_file="../../data/processed/DPEFs/dpef_paragraphs_sentences.csv",
                       pickle_file="../../data/model/words_scorer.pckl",
                       method="bm25"):
    # load data
    df = pd.read_csv(input_file, sep=";")
    documents = df["sentence"].values.tolist()

    # load *small* nlp parser for pos tagging
    if not spacy.util.is_package("fr_core_news_sm"):
        print("Downloading fr_core_news_sm spacy model for pos tagging...")
        spacy.cli.download('fr_core_news_sm')
        print("done.")
    nlp = spacy.load('fr_core_news_sm')

    # index
    scorer = Scoring.create("bm25")
    documents_words = []
    for doc in nlp.pipe(documents, disable=["parser", "ner"]): # only tagger is kept
        documents_words.append([token.text for token in doc if token.pos_])
    print("Indexing from {} sentences with {} as method".format(len(documents_words), method))
    scorer.index(documents_words)

    # save
    print("Saving scorer.")
    with open(pickle_file, "wb") as f:
        pickle.dump(scorer, f)

    return scorer


def load_scoring(pickle_file="../../data/model/words_scorer.pckl",
                 force_creation = False):
    """ Load it or initialize it if it does not exist"""
    if force_creation:
        scorer = initialize_scoring()
        return scorer
    try:
        f = open(pickle_file, "rb")
    except FileNotFoundError:
        print("Scorer not found and thus created (at address: {})".format(pickle_file))
        scorer = initialize_scoring() # TODO: add kwargs
    else:
        print("Load scorer from {}".format(pickle_file))
        scorer = pickle.load(f)

    return scorer


def initialize_weighted_vectorizer():
    # load scoring method

    # instantiate

    # save
    # TODO:     https://spacy.io/usage/saving-loading
    # add custom extension for vectorization
    # set extension to teh Doc used (is it saved also ???) with a method that accept another embedding
    # (cf. https://explosion.ai/blog/spacy-v2-pipelines-extensions

    return weighted_vectorizer


def load_weighted_vectorizer():
    """ Load it or initialize it if it does not exist"""
    return weighted_vectorizer


# test only:
print(load_scoring(force_creation=True).weights("Ceci est un test pollution marine".split()))

# the object to import to transform a string.)
# TODO: uncomment for use
# weighted_vectorizer = load_weighted_vectorizer()
