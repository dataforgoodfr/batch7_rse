from django.core.management.base import BaseCommand
import pickle
import base64
from polls import nlp, model_directory, Config, DebugConfig
from polls.models import ActivitySector, Company, DPEF, Sentence
from pdf_parser import get_companies_metadata_dict, get_list_of_pdfs_filenames, get_sentences_dataframe_from_pdf, \
    extract_company_metadata


# TODO: add argument "mode" to alow for debug - this will replace the usage of main.
# TODO: make the training of model based on the sql database and not on anything else.
def get_or_create_company_and_sectors(project_denomination: str, company_name: str, sectors_list: list):
    """ If company x sectors does not exist, create it and return the company object"""
    # TODO: make ActivitySector unique - done
    # TODO: delete introduction field ?
    company, newly_created = Company.objects.get_or_create(name=company_name,
                                                           pdf_name=project_denomination,
                                                           introduction="")
    if newly_created:
        activity_sectors = [ActivitySector.objects.get_or_create(name=my_sector_name)[0]
                            for my_sector_name in sectors_list]
        for activity_sector in activity_sectors:
            company._activity_sectors.set([activity_sector])

    return company


def add_sentence(sentence_row, dpef_instance):
    # do one sentence first
    # parse
    sentence = sentence_row["sentence"]
    context = sentence_row["paragraph"]
    page = int(sentence_row["page_nb"])
    # TODO: include 3 next lines as a getter of nlp object
    #  , or create a specific field Vector for it
    vector = nlp(sentence).vector
    np_bytes = pickle.dumps(vector)
    np_base64 = base64.b64encode(np_bytes)
    Sentence.objects.create(reference_file=dpef_instance,
                            text=sentence,
                            page=page,
                            context=context,
                            _vector=np_base64)


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--mode',
            choices=["debug", "final"],
            help='Whether to use a small fraction of data to debug or all of it.')

    def handle(self, **options):

        if options["mode"] == "debug":
            config = DebugConfig(model_directory)
        else:
            config = Config(model_directory)

        companies_metadata_dict = get_companies_metadata_dict(config)
        all_dpef_path = get_list_of_pdfs_filenames(config.dpef_dir)
        all_dpef_path = [input_file for input_file in all_dpef_path if
                           input_file.name.split("_")[0] in companies_metadata_dict.keys()]

        # TODO: consider parallelization
        for dpef_path in all_dpef_path:
            company_name, project_denomination, company_sectors, document_year, rse_ranges \
                = extract_company_metadata(dpef_path, companies_metadata_dict)

            # get or create company and its sectors
            company_instance = get_or_create_company_and_sectors(project_denomination,
                                                                 company_name,
                                                                 company_sectors)

            # create the DPEF instance
            dpef_instance, newly_created = DPEF.objects.get_or_create(company=company_instance,
                                                                      file_object=str(dpef_path),
                                                                      year=document_year)
            if newly_created:
                print("Start parsing for file: {}".format(dpef_path))
                df_sent = get_sentences_dataframe_from_pdf(config, dpef_path)
                df_sent.apply(lambda row: add_sentence(row, dpef_instance),
                              axis=1)
                print("finished")
            else:
                print("File is already included: {}".format(dpef_path))
            # print(Sentence.objects.all())
