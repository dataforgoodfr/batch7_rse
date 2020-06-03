"""
Scoring module
"""
# imports
import math
import pickle
import copy
import numpy as np
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from spacy.tokens import Doc
import enum

# Global parameters
# Approach: learn that they are common (i.e. keep for scorer), but ignore them in final vectorization.
IGNORED_POS = ['PRON', 'AUX', 'DET', "PUNCT"]
# TODO: add a list of stop words to ignore -> il existe des dictionnaires tous faits !


@enum.unique
class ScoringMethod(enum.Enum):

    BM25 = 1
    SIF = 2
    TFDIF = 3


class Scoring(object):
    """
    Base scoring object. Default method scores documents using TF-IDF.
    """

    @staticmethod
    def create(method):
        """
        Factory method to construct a Scoring object.

        Args:
            method: scoring method (bm25, sif, tfidf)

        Returns:
            Scoring object
        """

        if method == ScoringMethod.BM25:  # "bm25":
            return BM25()
        elif method == ScoringMethod.SIF:  # "sif":
            return SIF()
        elif method == ScoringMethod.TFDIF:  # "tfidf":
            # Default scoring object implements tf-idf
            return Scoring()

        return None

    def __init__(self):
        """
        Initializes backing statistic objects.
        """

        # Document stats
        self.total = 0
        self.tokens = 0
        self.avgdl = 0

        # Word frequency
        self.docfreq = Counter()
        self.wordfreq = Counter()
        self.avgfreq = 0

        # IDF index
        self.idf = {}
        self.avgidf = 0

        # Tag boosting
        self.tags = Counter()

    def index(self, documents):
        """
        Indexes a collection of documents using a scoring method

        Args:
            documents: input documents
        """

        # Calculate word frequency, total tokens and total documents
        for tokens in documents:
            # Total number of times token appears, count all tokens
            self.wordfreq.update(tokens)

            # Total number of documents a token is in, count unique tokens
            self.docfreq.update(set(tokens))

            # Total document count
            self.total += 1

        # Calculate total token frequency
        self.tokens = sum(self.wordfreq.values())

        # Calculate average frequency per token
        self.avgfreq = self.tokens / len(self.wordfreq.values())

        # Calculate average document length in tokens
        self.avgdl = self.tokens / self.total

        # Compute IDF scores
        for word, freq in self.docfreq.items():
            self.idf[word] = self.computeIDF(freq)

        # Average IDF score per token
        self.avgidf = sum(self.idf.values()) / len(self.idf)

    def weights(self, tokens):
        """
        Builds weight vector for each token in the input token.

        Args:
            document: (id, tokens, tags)

        Returns:
            list of weights for each token
        """

        # Weights array
        weights = []

        # Document length
        length = len(tokens)

        for token in map(lambda x: x.lower(), tokens):
            # Lookup frequency and idf score - default to averages if not in repository
            freq = self.wordfreq[token] if token in self.wordfreq else self.avgfreq
            idf = self.idf[token] if token in self.idf else self.avgidf

            # Calculate score for each token, use as weight
            weights.append(self.score(freq, idf, length))

        # Boost weights of tag tokens to match the largest weight in the list
        if self.tags:
            tags = {token: self.tags[token] for token in tokens if token in self.tags}
            if tags:
                maxWeight = max(weights)
                maxTag = max(tags.values())

                weights = [max(maxWeight * (tags[tokens[x]] / maxTag), weight)
                           if tokens[x] in tags else weight for x, weight in enumerate(weights)]

        return weights

    def load(self, path):
        """
        Loads a saved Scoring object from path.

        Args:
            path: directory path to load model
        """

        with open("%s/scoring" % path, "rb") as handle:
            self.__dict__.update(pickle.load(handle))

    def save(self, path):
        """
        Saves a Scoring object to path.

        Args:
            path: directory path to save model
        """

        with open("%s/scoring" % path, "wb") as handle:
            pickle.dump(self.__dict__, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def computeIDF(self, freq):
        """
        Computes an idf score for word frequency.

        Args:
            freq: word frequency

        Returns:
            idf score
        """

        return math.log(self.total / (1 + freq))

    # pylint: disable=W0613
    def score(self, freq, idf, length):
        """
        Calculates a score for each token.

        Args:
            freq: token frequency
            idf: token idf score
            length: total number of tokens in source document

        Returns:
            token score
        """

        return idf


class BM25(Scoring):
    """
    BM25 scoring. Scores using Apache Lucene's version of BM25 which adds 1 to prevent
    negative scores.
    """

    def __init__(self, k1=0.1, b=0.75):
        super(BM25, self).__init__()

        # BM25 configurable parameters
        self.k1 = k1
        self.b = b

    def computeIDF(self, freq):
        # Calculate BM25 IDF score
        return math.log(1 + (self.total - freq + 0.5) / (freq + 0.5))

    def score(self, freq, idf, length):
        # Calculate BM25 score
        k = self.k1 * ((1 - self.b) + self.b * length / self.avgdl)
        return idf * (freq * (self.k1 + 1)) / (freq + k)


class SIF(Scoring):
    """
    Smooth Inverse Frequency (SIF) scoring.
    """

    def __init__(self, a=0.001):
        super(SIF, self).__init__()

        # SIF configurable parameters
        self.a = a

    def score(self, freq, idf, length):
        # Calculate SIF score
        return self.a / (self.a + freq / self.tokens)


class VectorizerComponent(object):
    """
        Custom Spacy pipeline component that include scorer and overwrite calculation of Doc.vector.
    """
    name = "vectorizer_component"

    def __init__(self):
        self.data = {}
        self.IGNORED_POS = IGNORED_POS

    def add_scorer(self, scorer):
        self.data["scorer"] = copy.deepcopy(scorer)

    def __call__(self, doc):
        " Score each non-punctuation token from spacy doc, and overwrite the vector representation using BM25 weights"
        word_tokens = [token.text for token in doc if token.pos_ not in self.IGNORED_POS]
        word_vectors = [token.vector for token in doc if token.pos_ not in self.IGNORED_POS]
        weights = self.data["scorer"].weights(word_tokens)
        doc.vector = np.average(word_vectors, weights=np.array(weights, dtype=np.float32), axis=0)
        return doc

    def to_disk(self, path, **kwargs):
        data_path = path / "words_scorer.pckl"
        print("Saving Spacy vectorizer component to folder {}.".format(data_path))
        with open(data_path, "wb") as f:
            pickle.dump(self.data["scorer"], f)

    def from_disk(self, path, **kwargs):
        data_path = path / "words_scorer.pckl"
        print("Loading scorer from folder {}.".format(data_path))
        with open(data_path, "rb") as f:
            self.data["scorer"] = pickle.load(f)


# Add entry point to access the custom component and loading the model.
spacy.language.Language.factories["vectorizer_component"] = lambda nlp, **cfg: VectorizerComponent()


def similarity_to_vector(doc, vector):
    """
    Extension method to Doc objects that return the cosine similarity.
    :param doc: a doc obtained from a spacy model
    :param vector: a vector of same dimension (numpy array).
    :return: cosine similarity (float)
    """
    if vector is None:
        raise ValueError("Forgotten 'vector' argument.")
    vec1 = doc.vector
    vec2 = vector
    return cosine_similarity(vec1.reshape(1, -1), vec2.reshape(1, -1))[0][0]


spacy.tokens.Doc.set_extension("similarity_to_vector", method=similarity_to_vector)
