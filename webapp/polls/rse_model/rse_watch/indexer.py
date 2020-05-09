# general imports
import pandas as pd
import os
import shutil
import pickle
from pathlib import Path
import fr_core_news_md

# local import
from rse_watch.scoring import Scoring, VectorizerComponent, spacy
# NB: This import of spacy has custom extension to Doc object


def empty_directory(path_to_dir):
    """ Util function to delete the inside of a dir e.g. deleting data/model/* """
    for root, dirs, files in os.walk(path_to_dir):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def initialize_scorer(conf):
    # load data
    df = pd.read_csv(conf.parsed_sent_file, sep=";")

    documents = df["sentence"].values.tolist()

    # load *small* nlp parser for pos tagging
    if not spacy.util.is_package("fr_core_news_sm"):
        print("Downloading fr_core_news_sm spacy model for pos tagging...")
        spacy.cli.download('fr_core_news_sm')
        print("done.")
    nlp = spacy.load('fr_core_news_sm')


    # index
    scorer = Scoring.create(conf.SCORING_METHOD)
    documents_words = []
    for doc in nlp.pipe(documents, disable=["parser", "ner"]):  # only tagger is needed here
        documents_words.append([token.text for token in doc if token.pos_ != "PUNCT"])
    print("Indexing from {} sentences with {} as method".format(len(documents_words), conf.SCORING_METHOD))
    scorer.index(documents_words)

    # save
    print("Saving scorer.")
    pickle_path = Path(conf.scorer_pickle_file).parent
    pickle_path.mkdir(parents=True, exist_ok=True)
    with open(conf.scorer_pickle_file, "wb") as f:
        pickle.dump(scorer, f)

    return scorer


def load_scorer(conf):
    """ Load it or initialize it if it does not exist"""
    try:
        f = open(conf.scorer_pickle_file, "rb")
    except FileNotFoundError:
        print("Scorer not found and thus created (at address: {})".format(conf.scorer_pickle_file))
        scorer = initialize_scorer(conf)
    else:
        print("Loading scorer from {}".format(conf.scorer_pickle_file))
        scorer = pickle.load(f)
    return scorer


# TODO: add kwargs like method, paths...
def initialize_weighted_vectorizer(conf):
    print("Initializing weighted vectorizer.")
    # load scoring method or create it if not existing
    scorer = load_scorer(conf)
    # instantiate
    if not spacy.util.is_package("fr_core_news_md"):
        print("Downloading fr_core_news_md spacy model for pos tagging...")
        spacy.cli.download('fr_core_news_md')
        print("done.")
    nlp_wv = fr_core_news_md.load()
    nlp_wv.remove_pipe("ner")  # no need, and it seems not implemented for french model
    vectorizer_component = VectorizerComponent()
    vectorizer_component.add_scorer(scorer)
    nlp_wv.add_pipe(vectorizer_component)
    # save
    nlp_wv.to_disk(conf.model_dir)
    return nlp_wv


def load_weighted_vectorizer(conf,
                             create_from_scratch=False):
    """ Load custom spacy model, which should be created beforehand
    To use the returned 'nlp' model:
        # doc = nlp_wv("Une phrase simple avec des mots")
        # numpy_vector_of_the_sentence = doc.vector
        # similarity = doc.similarity_to_vector(another_numpy_vector)
    """
    if create_from_scratch:
        print("Initialization from scratch. [force_creation is set to 'True']")
        empty_directory(conf.model_dir)
        nlp = initialize_weighted_vectorizer(conf)
        return nlp
    try:
        print("Loading weighted vectorizer.")
        nlp = spacy.load(conf.model_dir)
        print("Loaded.")
    except FileNotFoundError as e:
        print("Model needs to be created first.")
        nlp = initialize_weighted_vectorizer(conf)
    except Exception as e:
        print("An error occured while loading weighted vectorizer:")
        print(e)
        print("We recreate the model from scratch and save it.")
        nlp = initialize_weighted_vectorizer(conf)
    return nlp


def run(config):
    """"""
    # TEST_MODE = True  # TODO: delete when in production.
    # if TEST_MODE:
    #     nlp = load_weighted_vectorizer(Config, create_from_scratch=True)
    #     print(nlp("Ceci est un test pollution marine").vector.sum())
    #     print(nlp("Ceci est un test pollution marine")._.similarity_to_vector(nlp("Ceci est un test pollution marine error").vector))

    nlp = load_weighted_vectorizer(config)
    # Usage:
    # doc = nlp_wv("Une phrase simple avec des mots")
    # numpy_vector_of_the_sentence = doc.vector
    # similarity = doc.similarity_to_vector(another_numpy_vector)
    return nlp
