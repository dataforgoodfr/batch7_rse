# Generated by Django 3.0.5 on 2020-06-07 15:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sentence',
            name='_weight',
            field=models.FloatField(default=-1, help_text='Poids de la phrase, donnée par le poids BM25 de ses constituants.', verbose_name='Weight'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='company',
            name='pdf_name',
            field=models.CharField(help_text="nNom de l'entreprise tel que trouvé dans le nom du fichier pdf. Permet en outre de pouvoir automatiser la lecture des PDFs et de les faire correspondre à la bonne entreprise.", max_length=20, unique=True, verbose_name='Nom PDF'),
        ),
    ]
