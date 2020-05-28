from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import models as dm  # django models
from django.db.models.fields.files import FieldFile
from scipy import spatial
from datetime import date
import os
from polls import nlp
import pickle
import base64


class ActivitySector(dm.Model):
    name = dm.CharField(max_length=50,
                        verbose_name=_("Nom du secteur"),
                        help_text=_("Nom du secteur"),
                        unique=True)

    def __str__(self):
        return self.name


class Company(dm.Model):
    name = dm.CharField(max_length=50, unique=True,
                        verbose_name=_("Nom"), help_text=_("Nom complet de l'entreprise"))
    pdf_name = dm.CharField(max_length=20, unique=True,
                            verbose_name=_("Nom PDF"),
                            help_text=_("Nom de l'entreprise tel que trouvé dans le nom du fichier pdf. "
                                        "Permet en outre de pouvoir automatiser la lecture des PDFs et de les "
                                        "faire correspondre à la bonne entreprise."))
    _activity_sectors = dm.ManyToManyField(ActivitySector,
                                           verbose_name=_("Secteurs"),
                                           help_text=_("Secteurs dans lesquels l'entreprise opére"))
    introduction = dm.TextField(default="",
                                verbose_name=_("Introduction"),
                                help_text=_("Quelques phrases permettant de décrire brièvement l'entreprise."))

    @property
    def dpefs(self):
        return DPEF.objects.filter(company__id=self.id)

    @property
    def sectors(self):
        return self._activity_sectors.all()

    def __str__(self):
        return self.name


def _validate_file_extension(value: FieldFile):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf']
    if ext not in valid_extensions:
        raise ValidationError(u'File not supported!')


class DPEF(dm.Model):
    file_name = dm.CharField(max_length=100,
                             primary_key=True,
                             unique=True,
                             verbose_name=_("Nom du fichier PDF"),
                             help_text=_("Nom complet du pdf de la DPEF, avec extension '.pdf'.."))
    company = dm.ForeignKey(Company, on_delete=dm.CASCADE,
                            verbose_name=_("Entreprise"), help_text=_("L'entreprise référencée par le document."))

    # TODO: adding MEDIA_ROOT and MEDIA_URL into the setting file (search for details...)
    file_object = dm.FileField(unique=True,
                               validators=[_validate_file_extension],
                               upload_to='polls/models/dpef/',
                               verbose_name=_("Fichier PDF"),
                               help_text=_("Document DPEF ou DDR au format PDF."))

    year = dm.IntegerField(choices=[(i, i) for i in range(1990, date.today().year + 1)],  # list of years since 1990
                           verbose_name=_("Année"), help_text=_("Année de référence du document DPEF"))

    def sentences(self):
        return Sentence.objects.filter(reference_file__id=self.id)

    def __str__(self):
        return self.file_object.name  # file path


class Sentence(dm.Model):
    reference_file = dm.ForeignKey(DPEF, on_delete=dm.CASCADE,
                                   verbose_name=_("Fichier"), help_text=_("Document contenant la phrase"))
    text = dm.TextField(verbose_name=_("Texte"), help_text=_("Texte de la phrase"))
    # better way to do this: https://stackoverflow.com/a/1113039
    text_tokens = dm.TextField(verbose_name=_("Tokens"),
                               help_text=_("Tokens du texte de la phrase, "
                                           "sous forme de string et séparé par des pipe |"))
    page = dm.PositiveIntegerField(verbose_name=_("Page"),
                                   help_text=_("Page sur laquelle se situe la phrase. "
                                               "Si la phrase est étalée sur plusieur pages, "
                                               "mettre la page de départ."))
    context = dm.TextField(verbose_name=_("Contexte"),
                           help_text=_("Paragraphe contenant la phrase. "
                                       "Permet de redonner du contexte à la phrase."))
    _vector = dm.BinaryField(null=True, blank=True)  # Vector(null=True, blank=True)


    def get_tokens(self):
        """Get the tokens stored in text_tokens"""
        tokens = self.text_tokens.split("|")
        return tokens

    def _construct_vector(self, nlp_vectorizer):
        vec = nlp_vectorizer(self.text).vector  # construct vector from self.text
        np_bytes = pickle.dumps(vec)
        np_base64 = base64.b64encode(np_bytes)
        self._vector = np_base64
        self.save()

    # def clean(self):
    #     super().clean()
    #     self._construct_vector()

    @property
    def vector(self):
        np_bytes = base64.b64decode(self._vector)
        vec = pickle.loads(np_bytes)
        return vec

    def similarity(self, sentence):
        return self.similarity_vector(self.vector, sentence.vector)

    @staticmethod
    def similarity_vector(vector1, vector2):
        print(spatial.distance.cosine(vector1, vector2))
        return 1 - spatial.distance.cosine(vector1, vector2)

    def __str__(self):
        return self.text

