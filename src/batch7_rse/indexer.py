# general imports
import pandas as pd
import numpy as np
import pickle

# local import
from scoring import Scoring, VectorizerComponent, similarity_to_vector
from scoring import spacy  # This import of spacy has custom extension to DOc object


# TODO: use a conf file to have unique file paths
def initialize_scorer(input_file="../../data/processed/DPEFs/dpef_paragraphs_sentences.csv",
                      pickle_file="../../data/model/vectorizer_component/words_scorer.pckl",
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


def load_scorer(pickle_file="../../data/model/vectorizer_component/words_scorer.pckl",
                force_creation=False):
    """ Load it or initialize it if it does not exist"""
    if force_creation:
        scorer = initialize_scorer() # TODO: add kwargs
        return scorer
    try:
        f = open(pickle_file, "rb")
    except FileNotFoundError:
        print("Scorer not found and thus created (at address: {})".format(pickle_file))
        scorer = initialize_scorer() # TODO: add kwargs
    else:
        print("Loading scorer from {}".format(pickle_file))
        scorer = pickle.load(f)
    return scorer


# TODO: add kwargs like method, paths...
def initialize_weighted_vectorizer(model_path="../../data/model/",
                                   force_creation=True):
    # load scoring method or create it if not existing
    scorer = load_scorer(force_creation = force_creation)
    # instantiate
    if not spacy.util.is_package("fr_core_news_md"):
        print("Downloading fr_core_news_md spacy model for pos tagging...")
        spacy.cli.download('fr_core_news_md')
        print("done.")
    nlp_wv = spacy.load('fr_core_news_md')
    nlp_wv.remove_pipe("ner")  # no need, and it seems not implemented for french model
    vectorizer_component = VectorizerComponent()
    vectorizer_component.add_scorer(scorer)
    nlp_wv.add_pipe(vectorizer_component)
    # save
    nlp_wv.to_disk(model_path)
    return nlp_wv


def load_weighted_vectorizer(model_path="../../data/model/"):
    """ Load custom spacy model, which should be created beforehand"""
    print("Loading weighted vectorizer.")
    nlp_wv = spacy.load(model_path)
    print("Loaded.")
    return nlp_wv


if __name__ == "__main__":
    # test only:
    # print(load_scoring(force_creation=True).weights("Ceci est un test pollution marine".split()))
    # nlp = initialize_weighted_vectorizer(model_path = "../../data/model/",
    #                                      force_creation=True)
    nlp = load_weighted_vectorizer(model_path = "../../data/model/")
    print(nlp("Ceci est un test pollution marine").vector.sum())
    print(nlp("Ceci est un test pollution marine")._.similarity_to_vector(nlp("Ceci est un test pollution marine error").vector))

    # the object to import to transform a string.)
    # TODO: uncomment for use
    # weighted_vectorizer = load_weighted_vectorizer()

