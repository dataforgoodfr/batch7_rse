
SCORING_METHOD = "bm25"  # other options are: "sif", "tfidf"  # TODO: add to conf file or not ?


class Config:
    dpef_dir = "../data/input/DPEFs/"
    annotations_file = "../data/input/Entreprises/entreprises_rse_annotations.csv"
    parsed_par_file = "../data/processed/DPEFs/dpef_paragraphs.csv"
    parsed_sent_file = "../data/processed/DPEFs/dpef_paragraphs_sentences.csv"
    model_dir = "../polls/rse_model/data/model/"
    scorer_pickle_file = model_dir + "vectorizer_component/words_scorer.pckl"


# smaller task for debug/tests
class DebugConfig:
    dpef_dir = "../data/input/DPEFs/Energéticien/"
    annotations_file = "../data/input/Entreprises/entreprises_rse_annotations.csv"
    parsed_par_file = "../polls/rse_model/data/processed/DPEFs/dpef_paragraphs_debug.csv"
    parsed_sent_file = "../polls/rse_model/data/processed/DPEFs/dpef_paragraphs_sentences_debug.csv"
    model_dir = "../polls/rse_model/data/model_debug/"
    scorer_pickle_file = model_dir + "vectorizer_component/words_scorer.pckl"
