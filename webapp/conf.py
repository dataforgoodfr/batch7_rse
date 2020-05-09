

# TODO: add an abstract class interface from which the other heritate

class Config:
    dpef_dir = "webapp/data/model/DPEFs/"
    annotations_file = "webapp/data/model/companies/companies_metadata.csv"
    parsed_par_file = "webapp/data/model/DPEFs/__parsed_dpefs__/dpef_paragraphs.csv"
    parsed_sent_file = "webapp/data/model/DPEFs/__parsed_dpefs__/dpef_sentences.csv"
    model_dir = "webapp/data/model/Model/"
    scorer_pickle_file = model_dir + "vectorizer_component/words_scorer.pckl"
    SCORING_METHOD = "bm25"


# smaller task for debug/tests
class DebugConfig:
    dpef_dir = "webapp/data/model/DPEFs/Energéticien/"
    annotations_file = "webapp/data/model/companies/companies_metadata.csv"
    parsed_par_file = "webapp/data/model/DPEFs/__parsed_dpefs__/(DEBUG)-dpef_paragraphs.csv"
    parsed_sent_file = "webapp/data/model/DPEFs/__parsed_dpefs__/(DEBUG)-dpef_sentences.csv"
    model_dir = "webapp/data/model/(DEBUG)-Model/"
    scorer_pickle_file = model_dir + "vectorizer_component/words_scorer.pckl"
    SCORING_METHOD = "bm25"
