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
config = Config(model_directory)

# Load the model
# N.B. model should be created prior to this,
# USe 'python manage.py index_sentences' to do so.
# TODO: Currently this is called even when populate_db is called and even
#  before flush is called. This is
#  a bit weird: parsing should be done once, and then the model created
#  and then the model used by the server !
#  --> This is not the right place for load_weighted_vectorizer.
documents = []
# nlp = load_weighted_vectorizer(config,
#                                documents,
#                                create_from_scratch=False)

# # TODO: delete fake nlp for debug
class nlp:
    def __init__(self, sentence):
        self.vector = np.random.random((100,))
