

class Config:
    dpef_dir = "./data/model/input/DPEFs/"
    annotations_file = "./data/model/input/Entreprises/entreprises_rse_annotations.csv"
    parsed_par_file = "./data/processed/DPEFs/dpef_paragraphs.csv"
    parsed_sent_file = "./data/processed/DPEFs/dpef_paragraphs_sentences.csv"
    model_dir = "./data/model/"
    scorer_pickle_file = model_dir + "vectorizer_component/words_scorer.pckl"
    SCORING_METHOD = "bm25"


# smaller task for debug/tests
class DebugConfig:
    dpef_dir = "./data/model//input/DPEFs/Energéticien/"
    annotations_file = "./data/model//input/Entreprises/entreprises_rse_annotations.csv"
    parsed_par_file = "./data/model//processed/DPEFs/dpef_paragraphs_debug.csv"
    parsed_sent_file = "./data/model//processed/DPEFs/dpef_paragraphs_sentences_debug.csv"
    model_dir = "./data/model//model_debug/"
    scorer_pickle_file = model_dir + "vectorizer_component/words_scorer.pckl"
    SCORING_METHOD = "bm25"
