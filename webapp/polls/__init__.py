
import sys
import os
from pathlib import Path
dir_path = Path(os.getcwd())
print(dir_path)
# Importing rse_watch package
sys.path.append(str(dir_path / 'polls/rse_model'))

from rse_watch.conf import Config
from rse_watch.indexer import load_weighted_vectorizer

model_directory = dir_path / "data/model"
nlp = load_weighted_vectorizer(Config(model_directory))




