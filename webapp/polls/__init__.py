# TODO: maybe all this could be removed, and loading the model done in specific commands
#  like in populate_db.
import numpy as np
import sys
import os
from pathlib import Path

# Importing rse_watch package
dir_path = Path(os.getcwd())
sys.path.append(str(dir_path / 'polls/rse_model'))

from rse_watch.conf import Config, DebugConfig
from rse_watch.indexer import load_weighted_vectorizer

model_directory = dir_path / "data/model"
# config = Config(model_directory)
# nlp = load_weighted_vectorizer(config)


# TODO: delete fake nlp for debug
class nlp:
    def __init__(self, sentence):
        self.vector = np.random.random((100,))
