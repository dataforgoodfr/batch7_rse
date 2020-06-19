# TODO: maybe all this could be removed, and loading the model done in specific commands
#  like in populate_db and
import numpy as np
import sys
import os
from pathlib import Path

# Importing rse_watch package and config
dir_path = Path(os.getcwd())
sys.path.append(str(dir_path / 'polls/rse_model'))
model_directory = dir_path / "data/model"
from rse_watch.conf import Config, DebugConfig
from rse_watch.indexer import load_weighted_vectorizer

nlp = None

# class nlp:
#     vector = np.random.random((300,))
#
#     def __init__(self, query):
#         pass

if any(command in sys.argv for command in ['gunicorn', 'runserver']):
    config = Config(model_directory)
    nlp = load_weighted_vectorizer(config, None, create_from_scratch=False)
