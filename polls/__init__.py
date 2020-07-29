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

nlp = "a"

print(sys.argv)
if not {'collectstatic', 'populate_db', "flush"}.intersection(sys.argv):
    config = Config(model_directory)
    nlp = load_weighted_vectorizer(config,
                                 [],  # should be created at deployment
                                 create_from_scratch=False)
    # todo: revert when dev finished
    # class nlp:
    #     vector = np.random.random((300,))
    #
    #     def __init__(self, query):
    #         pass
