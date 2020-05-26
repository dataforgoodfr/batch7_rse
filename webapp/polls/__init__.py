import numpy as np
import sys
import os
from pathlib import Path

# Importing rse_watch package
dir_path = Path(os.getcwd())
sys.path.append(str(dir_path / 'polls/rse_model'))

from rse_watch.conf import Config
from rse_watch.indexer import load_weighted_vectorizer

model_directory = dir_path / "data/model"
config = Config(model_directory)
# nlp = load_weighted_vectorizer(config)


# TODO: delete fake nlp for debug
def nlp(_):
    return np.random.random((100,))



