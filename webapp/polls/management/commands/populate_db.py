from django.core.management.base import BaseCommand

from polls import nlp, config
from polls.models import ActivitySector, Company, DPEF, Sentence


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


class Command(BaseCommand):
    def handle(self, **options):
        # now do the things that you want with your models here
        print("Hello world populate")
        # utiliser la config pou accéder à tous les pdfs

        # for each dpef in the directory DPEFs, access basic data from metadata:
        input_file = config.dpef_dir / "Construction/eiffage_2018_ddr.pdf"
        year = 2018
        company_name = "Eiffage"
        project_denomination = "eiffage_test"
        sectors = ["Construction", "Other"]
        rse_ranges = ["(1,3)"]

        # get or create company and its sectors
        company = get_or_create_company_and_sectors(project_denomination, company_name, sectors)

        # create the DPEF instance
        dpef, created = DPEF.objects.get_or_create(company=company,
                                                   file_object=str(input_file),
                                                   year=year)  # TODO: change later
        print(Company.objects.all())

        # parse
        my_phrase = "cette phrase est longue test"
        my_vector = nlp(my_phrase)
