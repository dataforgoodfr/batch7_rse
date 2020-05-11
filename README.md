### General Description
We aim to give access to societal and environmental commitments and actions from large French corporations subject to extra-financial performance declaration (_Declaration de Performances Extra-Financières_, or DPEFs), based on public reference documents.

On [link_to_website](link_to_website) (FR), one can have access to: [WORK IN PROGRESS]
- A **PDFs Database** centralizing a collection of more than 150 extra-financial performances declaration from large French corporations.
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
