# general imports
import pandas as pd
import os
import pickle
from pathlib import Path

# local import
from scoring import Scoring, VectorizerComponent, similarity_to_vector
from scoring import spacy  # This import of spacy has custom extension to DOc object

SCORING_METHOD = "bm25"  # other options are: "sif", "tfidf"


# TODO: use a conf file to have unique file paths
def initialize_scorer(input_file="../../data/processed/DPEFs/dpef_paragraphs_sentences.csv",
                      pickle_file="../../data/model/vectorizer_component/words_scorer.pckl"):
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
    scorer = Scoring.create(SCORING_METHOD)
    documents_words = []
    for doc in nlp.pipe(documents, disable=["parser", "ner"]):  # only tagger is needed here
        documents_words.append([token.text for token in doc if token.pos_ != "PUNCT"])
    print("Indexing from {} sentences with {} as method".format(len(documents_words), SCORING_METHOD))
    scorer.index(documents_words)

    # save
    print("Saving scorer.")
    pickle_path = Path(pickle_file).parent
    pickle_path.mkdir(parents=True, exist_ok=True)
    with open(pickle_file, "wb") as f:
        pickle.dump(scorer, f)

    return scorer


def load_scorer(pickle_file="../../data/model/vectorizer_component/words_scorer.pckl",
                force_creation=False):
    """ Load it or initialize it if it does not exist"""
    if force_creation:
        scorer = initialize_scorer(pickle_file=pickle_file) # TODO: add kwargs
        return scorer
    try:
        f = open(pickle_file, "rb")
    except FileNotFoundError:
        print("Scorer not found and thus created (at address: {})".format(pickle_file))
        scorer = initialize_scorer(pickle_file=pickle_file)  # TODO: add kwargs
    else:
        print("Loading scorer from {}".format(pickle_file))
        scorer = pickle.load(f)
    return scorer


# TODO: add kwargs like method, paths...
def initialize_weighted_vectorizer(model_path="../../data/model/",
                                   force_creation=True):
    print("Initializing weighted vectorizer.")
    # load scoring method or create it if not existing
    scorer = load_scorer(force_creation=force_creation)
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


def load_weighted_vectorizer(model_path="../../data/model/",
                             force_creation=True):
    """ Load custom spacy model, which should be created beforehand"""
    if force_creation:
        print("[force_creation is set to 'True']")
        nlp = initialize_weighted_vectorizer(model_path=model_path,
                                                force_creation=force_creation)
        return nlp
    try:
        print("Loading weighted vectorizer.")
        nlp = spacy.load(model_path)
        print("Loaded.")
    except FileNotFoundError as e:
        print("Model needs to be created first.")
        nlp = initialize_weighted_vectorizer(model_path=model_path,
                                                force_creation=force_creation)
    except Exception as e:
        print("An error occured while loading weighted vectorizer:")
        print(e)
        print("We recreate the model from scratch and save it.")
        nlp = initialize_weighted_vectorizer(model_path=model_path,
                                                force_creation=force_creation)
    return nlp


nlp = load_weighted_vectorizer(model_path="../../data/model/",
                               force_creation=False)
# Usage:
# doc = nlp_wv("Une phrase simple avec des mots")
# numpy_vector_of_the_sentence = doc.vector
# similarity = doc.similarity_to_vector(another_numpy_vector)

TEST_MODE = True

if TEST_MODE:
    print(nlp("Ceci est un test pollution marine").vector.sum())
    print(nlp("Ceci est un test pollution marine")._.similarity_to_vector(nlp("Ceci est un test pollution marine error").vector))

