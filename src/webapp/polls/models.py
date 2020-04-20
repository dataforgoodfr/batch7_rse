from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import models
from datetime import date


class ActivitySector(models.Model):

    # class EnumerationSectorActivity(models.TextChoices):
    #     TERTIAIRE = 'Tertiaire', _('Tertiaire')

    name = models.CharField(
        max_length=50,
        # choices=EnumerationSectorActivity.choices,
        # default=SectorActivity.TERTIAIRE
    )

    def __str__(self):
        return self.name


class Company(models.Model):

    name = models.CharField(max_length=50, unique=True)
    # pdf_name = models.CharField(max_length=20)
    sectors = models.ManyToManyField(ActivitySector)
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
    start_rse_page = models.PositiveIntegerField()
    end_rse_page = models.PositiveIntegerField()

    @property
    def year(self):
        return self.date.year

    def clean(self):
        super().clean()
        if self.start_rse_page > self.end_rse_page:
            raise ValidationError(_("start page must be before end page !"))

    def __str__(self):
        return self.file_object.name  # file path


class Sentence(models.Model):

    file = models.ForeignKey(File, on_delete=models.CASCADE)
    sentence = models.TextField()
    startfilepage = models.PositiveIntegerField()
    endfilepage = models.PositiveIntegerField()
    is_RSE_sentence = models.BooleanField(default=False)
    # ...
    # put metadata fields here !

    def _set_rse(self):
        if self.startfilepage >= self.file.start_rse_page and self.endfilepage <= self.file.end_rse_page:
            self.is_RSE_sentence = True
        else:
            self.is_RSE_sentence = False

    def clean(self):
        super().clean()
        if self.startfilepage > self.endfilepage:
            raise ValidationError(_("start page must be before end page !"))
        self._set_rse()

    def __str__(self):
        return self.sentence
