# WHY : to allow multiprocessing with Pool.map()
import django

django.setup()

from django.core.management.base import BaseCommand
from django.core.files import File

from functools import partial
import multiprocessing as mp
import numpy as np
from tqdm import tqdm

from polls import model_directory, Config, DebugConfig
from polls.models import ActivitySector, Company, DPEF, Sentence
from rse_watch.pdf_parser import get_companies_metadata_dict, get_list_of_pdfs_filenames, \
    get_sentences_dataframe_from_pdf, \
    extract_company_metadata
from rse_watch.indexer import load_weighted_vectorizer


def add_company_and_sectors(project_denomination: str, company_name: str, sectors_list: list):
    """ If company x sectors does not exist, create it and return the company object"""
    # TODO: delete introduction field ?
    company, newly_created = Company.objects.get_or_create(name=company_name,
                                                           pdf_name=project_denomination,
                                                           introduction="")
    if newly_created:
        activity_sectors = [ActivitySector.objects.get_or_create(name=my_sector_name)[0]
                            for my_sector_name in sectors_list]
        # for activity_sector in activity_sectors:
        company._activity_sectors.set(activity_sectors)

    return company


def add_dpef(config, dpef_path):
    companies_metadata_dict = get_companies_metadata_dict(config)
    company_name, project_denomination, company_sectors, document_year, rse_ranges \
        = extract_company_metadata(dpef_path, companies_metadata_dict)

    # get or create company and its sectors
    company_instance = add_company_and_sectors(project_denomination,
                                               company_name,
                                               company_sectors)

    # create the DPEF instance if not existing
    try:
        DPEF.objects.get(file_name=dpef_path.name)
    except:
        with dpef_path.open("rb") as f:
            dpef_file = File(f, name=dpef_path.name)
            # TODO: verify that get_or_create check uniqueness of files
            dpef_instance, newly_created = DPEF.objects.get_or_create(file_name=dpef_path.name,
                                                                      company=company_instance,
                                                                      file_object=dpef_file,
                                                                      year=document_year)
        if newly_created:
            df_sent = get_sentences_dataframe_from_pdf(config, dpef_path)
            df_sent.apply(lambda row: add_sentence(row, dpef_instance),
                          axis=1)
        else:
            print("File is already in db: {}".format(dpef_path.name))


def add_sentence(sentence_row, dpef_instance):
    # do one sentence first
    # parse
    sentence = sentence_row["sentence"]
    sentence_tokens = sentence_row["sentence_tokens"]
    context = sentence_row["paragraph"]
    page = int(sentence_row["page_nb"])
    # NB: vector will be included afterwards
    Sentence.objects.create(dpef=dpef_instance,
                            text=sentence,
                            text_tokens=sentence_tokens,
                            page=page,
                            context=context)


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--mode',
            choices=["debug", "final"],
            default="final",
            help='Whether to use a small fraction of data to debug or all of it.')

        parser.add_argument(
            '--task',
            choices=["parse", "model", "parse_and_model"],
            default="parse_and_model",
            help='Whether to parse, train BM25 vectorizer model, or both.')

    def handle(self, **options):

        if options["mode"] == "debug":
            config = DebugConfig(model_directory)
        else:
            config = Config(model_directory)

        if options["task"] in ["parse", "parse_and_model"]:
            companies_metadata_dict = get_companies_metadata_dict(config)
            all_dpef_paths = get_list_of_pdfs_filenames(config.dpef_dir)
            all_dpef_paths = [input_file for input_file in all_dpef_paths if
                              input_file.name.split("_")[0] in companies_metadata_dict.keys()]

            # PARALLELIZATION
            parallel_add_dpef = partial(add_dpef, config)

            # TODO: need to change the DB to have real multiprocessing
            # n_cores = mp.cpu_count() - 1 or 1
            n_cores = 1
            with mp.Pool(n_cores) as pool:
                print("Multiprocessing with {} cores".format(n_cores))
                df_sents = list(
                    tqdm(
                        pool.imap(
                            parallel_add_dpef,
                            all_dpef_paths
                        ),
                        total=len(all_dpef_paths)
                    )
                )

        if options["task"] in ["model", "parse_and_model"]:
            # train the BM25 vectorizer
            try:
                documents = [sentence.get_tokens() for sentence in Sentence.objects.iterator()]
            except:
                print("Error while getting sentence object."
                      "Try running 'python manage.py populate_db --task parse_and_model'?")
                raise
            nlp = load_weighted_vectorizer(config, documents, create_from_scratch=True)
            # Update the _vector field of the sentence
            print("Vectorization of all sentences based on word embeddings and BM25.")
            for sentence in tqdm(Sentence.objects.iterator(), total=Sentence.objects.count()):
                sentence.construct_vector(nlp)

        print("Over for task {}".format(options["task"]))
