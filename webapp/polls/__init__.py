
import sys
import os
from pathlib import Path
dir_path = Path(os.getcwd())
# Importing rse_watch package
sys.path.append(str(dir_path / 'polls/rse_model'))

import conf
from rse_watch.indexer import load_weighted_vectorizer

model_directory = dir_path / "data/model"
nlp = load_weighted_vectorizer(conf.Config(model_directory))
