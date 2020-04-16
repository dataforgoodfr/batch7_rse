from django.utils.translation import gettext_lazy as _
from django.db import models


class Company(models.Model):

    class SectorActivity(models.TextChoices):
        TERTIAIRE = 'Tertiaire', _('Tertiaire')

    name = models.CharField(max_length=50)
    pdf_name = models.CharField(max_length=20)
    sector = models.CharField(
        max_length=50,
        choices=SectorActivity.choices,
        # default=SectorActivity.TERTIAIRE
    )
    introduction = models.TextField()


class File(models.Model):

    class FileType(models.TextChoices):
        DPEF = 'DPEF', _('dpef')
        RSE = 'RSE', _('responsabilité sociale et environnementale')

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    path = models.CharField(max_length=200)
    year = models.IntegerField(default=0)
    type = models.CharField(
        max_length=4,
        choices=FileType.choices,
        # default=FileType.DPEF
    )


class Sentence(models.Model):

    file = models.ForeignKey(File, on_delete=models.CASCADE)
    sentence = models.TextField()
    # ...
    # put metadata fields here !
