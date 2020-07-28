from pathlib import Path
from rse_watch.scoring import ScoringMethod


class Config:

    def __init__(self, src_model: Path):
        """
        Initialize model directories configurations from an absolute path.
        :param model_dir: Absolute path where model will be construc and saved.
        :type model_dir: Path or str. If str, will be cast into a pathlib.Path object
        """
        if type(src_model) is str:
            src_model = Path(src_model)
        self.src_model = src_model
        self.dpef_dir = self.src_model / "DPEFs/"
        self.annotations_file = self.src_model / "DPEFs/companies_metadata.csv"
        self.parsed_sent_file = self.src_model / "DPEFs/__parsed_dpefs__/dpef_sentences.csv"
        self.model_dir = self.src_model / "Model/"
        self.scorer_pickle_file = self.model_dir / "vectorizer_component/words_scorer.pckl"
        self.SCORING_METHOD = ScoringMethod.BM25
        self.MIN_NB_OF_WORDS = 3  # among words with non ignored pos


# smaller task for debug/tests
class DebugConfig(Config):

    def __init__(self, src_model: Path):
        """
        Initialize model directories for debug configurations from an absolute path.
        :param model_dir: Absolute path where model will be construc and saved.
        :type model_dir: Path or str. If str, will be cast into a pathlib.Path object
        """
        super().__init__(src_model)
        self.dpef_dir = self.src_model / "__DPEFs_debug__/"
        self.annotations_file = self.src_model / "DPEFs/companies_metadata_debug.csv"
        self.parsed_sent_file = self.src_model / "DPEFs/__parsed_dpefs__/dpef_sentences_debug.csv"
        self.model_dir = self.src_model / "__Model_debug__/"
        self.scorer_pickle_file = self.model_dir / "vectorizer_component/words_scorer.pckl"
