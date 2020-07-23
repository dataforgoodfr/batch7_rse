# General Description

We aim to give access to societal and environmental commitments and actions from large French corporations subject to extra-financial performance declaration (_Declaration de Performances Extra-Financières_, or DPEFs), based on public reference documents.

We propose the RSE Explorer tool, of which an in-depth description can be accessed via [data-for-good's projects page](https://dataforgood.fr/#projects).

RSE Explorer is a tool that gives access to:
- A **PDFs Database** centralizing a collection of about 135 extra-financial performances declaration from large French corporations. It can be downloaded through this [link](https://1drv.ms/u/s!Aj9j6X93cDjbhp0xJCntsQ8lMZsv2A?e=zi2cbS) and until the 21st of July 2021.
- The underlying **text Database**, downloadable in a structured csv format, enabling re-analyses of the underlying information contained in the PDFs.
- A smart **search engine** of the PDF's content, to be used as a technology watch tool for societal and environmental innovation.

Steps:
- Reference a set of larges corporations subject to this declaration (_via_ public databases and web searches; there is no official public listing)
- Collect their reference documents (large unstructured PDFs)
- Identify pages refering to environmental strategies and performances (labelling)
- Parse text from PDFs, keeping paragraph structure (PDFminer + sliding windows algorithms)
- Get sentences from text paragraphs, and add relevant metada to each sentence to enable filtering (e.g. presence of a year in the future) 
- Train a BM25 scorer to be able to give weights to words based on their frequency (in corpus and sentence).
- Build a custom NLP pipeline that takes a sentence, tokenize it, and turn it into a vector using pretrained Word2Vec embeddings and BM25 weights.
- Use similarity-based searches to allow for querying the DPEFs sentences.
- Deploy the solution on a website. 

# Installation

# Setting local development environment for python/Django.

You will need:
- python 3.6.8 (>3.1.0 might work, not tested)
- virtualenv or virtualenvwrapper ([installation steps](https://virtualenvwrapper.readthedocs.io/en/latest/))

To setup your local env using virtualenvwrapper use:

    mkvirtualenv rse_watch -r requirements.txt

If you want to source your virtual env:

    workon rse_watch
    
# Flushing the database
If you need to empty the database after some tests:

	cd webapp
	python manage.py flush

If the schema of your sql database is **outdated with the current schema**, you may want to restart it from scratch. Indeed, Django makes it mandatory to keep all old classes that appeared at least once in the db schema, and this can make the model messy in times of development.

To restart from scratch, you can follow scenario 1 in [this tutorial](https://simpleisbetterthancomplex.com/tutorial/2016/07/26/how-to-reset-migrations.html).

But Django will have trouble running makemigrations because some part of the model are used in various scripts (e.g. views.py) and Django NEEDs the tables to exist... before creating them. 

A hackky way to deal with that is to comment the lines that call classes of the data model:
- Comment all lines in views.py
- Comment all lines in forms.py
- Comment the content of list urlpatterns in urls.py
Then make the migrations (cf. step 3 in tutorial) and uncomment. 


# Parsing the pdfs and indexing the sentences with a BM25 model

The DPEFs must be parsed, and a Spacy pipeline that include a BM25 model must be saved.
There are custom Django commands to do so:

	cd webapp
	python manage.py populate_db
 
Of course debug mode is waaay faster:

	# or for full run and parsing:
	python manage.py populate_db --mode debug 

Other options:
 - task: parse, model, or task_and_model

# Running the server locally

The server can then started with:

    cd webapp
    python manage.py runserver --noreload --settings settings.dev

where noreload avoid double initialization.


# Deployment

The database is hosted on AWS.

The parsing of pdfs can be performed locally, and only needs to be performed when new pdfs are added.
Use:

	cd webapp
	python manage.py populate_db --settings settings.dev --task parse --mode final

The vectorizer model needs to be built directly in the deployment server, at each release, and the vectors in the database are updated in consequence.
