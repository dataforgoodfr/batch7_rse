# 
Objective: identifying all environmental engagements from large companies subject to extra-financial performance declaration, based on public reference documents.

Approach:
- Reference larges companies subject to this declaration (~250) (use public databases + manual completion
- Collect reference documents (usually 1 (sometimes 2/3) large unstructured PDFs) (find URLs
- Identify pages refering to environmental strategies and performances (manual labelling (followed by classification)
- Parse text from PDFs, keeping paragraph structure (PDFminer + sliding windows)
- Clean the text data for NLP algorithms
- Scope what kind of information defines an engagement (basic feature creation & filters, labelling)
- Train supervised model to identify such engagements 


# Installation

# Setting local development environment for python/Django.

You will need:
- python 3.6.8 (>3.1.0 might work, not tested)
- virtualenv or virtualenvwrapper ([installation steps](https://virtualenvwrapper.readthedocs.io/en/latest/))

To setup your local env using virtualenvwrapper use:

    mkvirtualenv rse_watch -r requirements.txt

If you want to source your virtual env:

    workon rse_watch
    
# Running the django server

Before running Django, the dpefs must be parsed. 
Currently, this is done by creating a file dpef_sentences.csv, which is then used to train the BM25 scorer and to save a Spacy model that can do weighted vectorization of sentences (therefore called "weighted vectorizer"). You can parse the PDFs and instantiate the model via:

    cd webapp
    python main.py

Hack to parse only a subset of the PDFs (still takes up to (6 minutes)):

	cd webapp
	python main.py --mode debug

The model is created under (DEBUG)-Model, but can be renamed to "Model" to be used by Django in debug phases.
Django can then be run with:

    cd webapp
    python manage.py runserver