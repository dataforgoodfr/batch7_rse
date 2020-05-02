from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.fields.files import FieldFile
from datetime import date
import os
import numpy as np


class ActivitySector(models.Model):

    name = models.CharField(max_length=50,
                            help_text=_("Nom du secteur"))

    def __str__(self):
        return self.name


class Company(models.Model):

    name = models.CharField(max_length=50, unique=True,
                            verbose_name=_("Nom"), help_text=_("Nom de l'entreprise"))
    pdf_name = models.CharField(max_length=20, unique=True,
                                verbose_name=_("Nom PDF"),
                                help_text=_("Nom de l'entreprise tel que trouvé dans le nom du fichier pdf. "
                                            "Permet en outre de pouvoir automatiser la lecture des PDFs et de les "
                                            "faire correspondre à la bonne entreprise."))
    sectors = models.ManyToManyField(ActivitySector,
                                     verbose_name=_("Secteurs"), help_text=_("Secteurs dans lesquels l'entreprise opére"))
    introduction = models.TextField(default="",
                                    verbose_name=_("Introduction"),
                                    help_text=_("Quelques phrases permettant de décrire brièvement l'entreprise."))

    def __str__(self):
        return self.name


class DPEF(models.Model):

    @staticmethod
    def _validate_file_extension(value: FieldFile):
        ext = os.path.splitext(value.name)[1]
        valid_extensions = ['.pdf']
        if ext not in valid_extensions:
            raise ValidationError(u'File not supported!')

    # class FileType(models.TextChoices):
    #     DPEF = 'DPEF', _('dpef')
    #     RSE = 'DDR', _('ddr')

    company = models.ForeignKey(Company, on_delete=models.CASCADE,
                                verbose_name=_("Entreprise"), help_text=_("L'entreprise référencée par le document."))

    # TODO: adding MEDIA_ROOT and MEDIA_URL into the setting file (search for details...)
    file_object = models.FileField(unique=True, validators=[_validate_file_extension],
                                   verbose_name=_("Fichier PDF"), help_text=_("Document DPEF ou DDR au format PDF."))

    year = models.IntegerField(choices=[(i, i) for i in range(1990, date.today().year + 1)],  # list of years since 1990
                               verbose_name=_("Année"), help_text=_("Année de référence du document DPEF"))

    # file_type = models.CharField(
    #     max_length=4,
    #     choices=FileType.choices,
    #     # default=FileType.DPEF
    # )

    def __str__(self):
        return self.file_object.name  # file path


class Sentence(models.Model):

    class Vector(models.TextField):

        # TODO: Test transformation from string to numpy array
        @staticmethod
        def to_numpy(value: str):
            return np.array([float(val) for val in value.split(' ')])

        def to_python(self, value):
            if isinstance(value, np.ndarray):
                return value

            if value is None:
                return value

            return self.to_numpy(value)

        # TODO: Test construction of a true vector list as a string
        @staticmethod
        def from_numpy(numpy_vector: np.ndarray):
            if isinstance(numpy_vector, np.ndarray):
                return ' '.join([val for val in numpy_vector])
            return None

    reference_file = models.ForeignKey(DPEF, on_delete=models.CASCADE,
                                       verbose_name=_("Fichier"), help_text=_("Document contenant la phrase"))
    text = models.TextField(verbose_name=_("Texte"), help_text=_("Texte de la phrase"))
    page = models.PositiveIntegerField(verbose_name=_("Page"),
                                       help_text=_("Page sur laquelle se situe la phrase. "
                                                   "Si la phrase est étalée sur plusieur pages, "
                                                   "mettre la page de départ."))
    context = models.TextField(verbose_name=_("Contexte"),
                               help_text=_("Paragraphe contenant la phrase. "
                                           "Permet de redonner du contexte à la phrase."))
    vector = Vector
    # put filtres here like this one :
    # exacts_words = models.BooleanField(default=False)

    def clean(self):
        super().clean()

    def __str__(self):
        return self.text
