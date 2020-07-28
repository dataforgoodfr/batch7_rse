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
from rse_watch.indexer import run as run_indexer

nlp = None

if {'common.wsgi', 'runserver'}.intersection(sys.argv):
    # Load config, and will load existing vectorizer if already exists, else will create it.
    config = Config(model_directory)
    nlp = run_indexer(config)  # todo : choose the right loading function, not run_indexer.

    # # # todo: revert when dev finished
    # class nlp:
    #     vector = np.random.random((300,))
    #
    #     def __init__(self, query):
    #         pass
