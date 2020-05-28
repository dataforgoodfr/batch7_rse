from django.core.management.base import BaseCommand
from polls import nlp, model_directory, Config, DebugConfig, load_weighted_vectorizer
from polls.models import ActivitySector, Company, DPEF, Sentence
import itertools


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--mode',
            choices=["debug", "final"],
            default="final",
            help='Whether to use a small fraction of data to debug or all of it.')

    def handle(self, **options):

        if options["mode"] == "debug":
            config = DebugConfig(model_directory)
            subset_of_sentences = itertools.islice(Sentence.objects.iterator(), 200)
            try:
                documents = [sentence.text for sentence in subset_of_sentences]
            except:
                print("Error while getting sentence object."
                      "Maybe try running 'python manage.py populate_db'?")
                raise
        elif options["mode"] == "final":
            config = Config(model_directory)
            try:
                documents = [sentence.text for sentence in Sentence.objects.iterator()]
            except:
                print("Error while getting sentence object."
                      "Maybe try running 'python manage.py populate_db'?")
                raise

        _ = load_weighted_vectorizer(config, documents, create_from_scratch=True)


