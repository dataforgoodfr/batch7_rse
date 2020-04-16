from django.utils.translation import gettext_lazy as _
from django.db import models
from datetime import date


class Company(models.Model):

    class SectorActivity(models.TextChoices):
        TERTIAIRE = 'Tertiaire', _('Tertiaire')

    name = models.CharField(max_length=50, unique=True)
    pdf_name = models.CharField(max_length=20)
    sector = models.CharField(
        max_length=50,
        choices=SectorActivity.choices,
        # default=SectorActivity.TERTIAIRE
    )
    introduction = models.TextField()

    def __str__(self):
        return self.name


class File(models.Model):

    class FileType(models.TextChoices):
        DPEF = 'DPEF', _('dpef')
        RSE = 'RSE', _('responsabilité sociale et environnementale')

    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    # TODO: adding MEDIA_ROOT and MEDIA_URL into the setting file (search for details...)
    file_object = models.FileField(unique=True)

    date = models.DateField(default=date.today)
    type = models.CharField(
        max_length=4,
        choices=FileType.choices,
        # default=FileType.DPEF
    )

    def __str__(self):
        return self.file_object.name  # file path

    @property
    def year(self):
        return self.date.year


class Sentence(models.Model):

    file = models.ForeignKey(File, on_delete=models.CASCADE)
    sentence = models.TextField()
    # ...
    # put metadata fields here !

    def __str__(self):
        return self.sentence
