from pathlib import Path
from polls.rse_model.rse_watch.scoring import ScoringMethod
# TODO: add an abstract class interface from which the other heritate


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
        self.annotations_file = self.src_model / "companies/companies_metadata.csv"
        self.parsed_par_file = self.src_model / "DPEFs/__parsed_dpefs__/dpef_paragraphs.csv"
        self.parsed_sent_file = self.src_model / "DPEFs/__parsed_dpefs__/dpef_sentences.csv"
        self.model_dir = self.src_model / "Model/"
        self.scorer_pickle_file = self.model_dir + "vectorizer_component/words_scorer.pckl"
        self.SCORING_METHOD = ScoringMethod.BM25  # "bm25"


# smaller task for debug/tests
class DebugConfig(Config):

    def __init__(self, src_model: Path):
        """
        Initialize model directories for debug configurations from an absolute path.
        :param model_dir: Absolute path where model will be construc and saved.
        :type model_dir: Path or str. If str, will be cast into a pathlib.Path object
        """
        super().__init__(src_model)
        self.dpef_dir = self.dpef_dir / "Energéticien/"
        self.parsed_par_file = self.src_model / "DPEFs/__parsed_dpefs__/(DEBUG)-dpef_paragraphs.csv"
        self.parsed_sent_file = self.src_model / "DPEFs/__parsed_dpefs__/(DEBUG)-dpef_sentences.csv"
        self.model_dir = self.src_model / "(DEBUG)-Model/"



    # dpef_dir = "data/model/DPEFs/Energéticien/"
    # annotations_file = "data/model/companies/companies_metadata.csv"
    # parsed_par_file = "data/model/DPEFs/__parsed_dpefs__/(DEBUG)-dpef_paragraphs.csv"
    # parsed_sent_file = "data/model/DPEFs/__parsed_dpefs__/(DEBUG)-dpef_sentences.csv"
    # model_dir = "data/model/(DEBUG)-Model/"
    # scorer_pickle_file = model_dir + "vectorizer_component/words_scorer.pckl"
    # SCORING_METHOD = "bm25"
