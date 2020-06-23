# general imports
import pandas as pd
import os, sys
import shutil
import pickle
from pathlib import Path
import fr_core_news_md

# local import
from rse_watch.scoring import Scoring, VectorizerComponent, spacy
# NB: This import of spacy has custom extension to Span and Doc object


def empty_directory(path_to_dir):
    """ Util function to delete the inside of a dir e.g. deleting data/model/* """
    for root, dirs, files in os.walk(path_to_dir):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def initialize_scorer(config, documents):
    """
    Initialize the BM25 scorer object, from a csv file with a sentence by row.
    """

    # # load *small* nlp parser for pos tagging
    # if not spacy.util.is_package("fr_core_news_sm"):
    #     print("Downloading fr_core_news_sm spacy model for pos tagging...")
    #     spacy.cli.download('fr_core_news_sm')
    #     print("done.")
    # nlp = spacy.load('fr_core_news_sm')

    # index
    scorer = Scoring.create(config.SCORING_METHOD)
    documents_words = documents
    # for doc in nlp.pipe(documents, disable=["parser", "ner"]):  # only tagger is needed here
    #     documents_words.append([token.text for token in doc if token.pos_ != "PUNCT"])
    print("Indexing from {} sentences with {} as method".format(len(documents_words), config.SCORING_METHOD))
    scorer.index(documents_words)

    # save
    print("Saving scorer.")
    pickle_path = Path(config.scorer_pickle_file).parent
    pickle_path.mkdir(parents=True, exist_ok=True)
    with open(config.scorer_pickle_file, "wb") as f:
        pickle.dump(scorer, f)
    print("Saved scorer.")
    return scorer


def load_scorer(conf, documents):
    """ Load it or initialize it if it does not exist"""
    try:
        f = open(conf.scorer_pickle_file, "rb")
    except FileNotFoundError:
        print("Scorer not found and thus created (at address: {})".format(conf.scorer_pickle_file))
        scorer = initialize_scorer(conf, documents)
    else:
        print("Loading scorer from {}".format(conf.scorer_pickle_file))
        scorer = pickle.load(f)
    return scorer


# TODO: add kwargs like method, paths...
def initialize_weighted_vectorizer(config, documents):
    print("Initializing weighted vectorizer.")
    # load scoring method or create it if not existing
    scorer = load_scorer(config, documents)
    # instantiate
    if not spacy.util.is_package("fr_core_news_md"):
        print("Downloading fr_core_news_md spacy model for pos tagging...")
        spacy.cli.download('fr_core_news_md')
        print("done.")
    print("Loading fr_core_news_md Spacy model.")
    nlp_wv = fr_core_news_md.load()
    nlp_wv.remove_pipe("ner")  # no need, and it seems not implemented for french model
    vectorizer_component = VectorizerComponent()
    vectorizer_component.add_scorer(scorer)
    nlp_wv.add_pipe(vectorizer_component)
    # save
    nlp_wv.to_disk(config.model_dir)
    print("added to disk (TODO: delete this statement")
    return nlp_wv


def load_weighted_vectorizer(config,
                             documents,
                             create_from_scratch=False):
    """ Load custom spacy model, which should be created beforehand
    To use the returned 'nlp' model:
        # doc = nlp_wv("Une phrase simple avec des mots")
        # numpy_vector_of_the_sentence = doc.vector
        # similarity = doc.similarity_to_vector(another_numpy_vector)
    """
    if create_from_scratch:
        print("Initialization from scratch. [force_creation is set to 'True']")
        empty_directory(config.model_dir)
        nlp = initialize_weighted_vectorizer(config, documents)
        return nlp
    try:
        print("Loading weighted vectorizer.")
        nlp = spacy.load(config.model_dir)
        print("Loaded.")
    except FileNotFoundError as e:
        print("Model needs to be created first.")
        nlp = initialize_weighted_vectorizer(config, documents)
    except Exception as e:
        print("An error occured while loading weighted vectorizer:")
        print(e)
        print("We recreate the model from scratch and save it.")
        nlp = initialize_weighted_vectorizer(config, documents)
    return nlp


def run(config, create_from_scratch=False):
    """ Called from main.py; this loads or create the weighted vectorizer via csv files. """
    # load data
    df = pd.read_csv(config.parsed_sent_file, sep=";")
    documents = df["sentence"].values.tolist()
    nlp = load_weighted_vectorizer(config, documents, create_from_scratch=create_from_scratch)
    # Usage:
    # doc = nlp_wv("Une phrase simple avec des mots")
    # numpy_vector_of_the_sentence = doc.vector
    return nlp
