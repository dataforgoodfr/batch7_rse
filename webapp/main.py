import os
import sys
from pathlib import Path
dir_path = Path(os.getcwd())
print(dir_path)
# Importing rse_watch package
sys.path.append(str(dir_path / 'polls/rse_model'))
model_directory = dir_path / "data/model"

from rse_watch.pdf_parser import run as run_parser
from rse_watch.indexer import run as run_indexer
from rse_watch.conf import Config, DebugConfig
from time import time
import argparse



def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--mode',
                        default="final",
                        choices=["final", "debug"],
                        help="Wether to parse all dpefs only a subset.")
    parser.add_argument('--task',
                        default="both",
                        choices=["both", "parser", "sententizer", "only_model"],
                        help="Which parsing task to run")
    args = parser.parse_args()
    if args.mode == "final":
        config = Config(model_directory)
    elif args.mode == "debug":
        config = DebugConfig(model_directory)
    t = time()

    print("Parsing and creating NLP scorer and vectorizer.")
    run_parser(config, task=args.task)
    run_indexer(config)

    print("Finished intialization")
    print("Took {} seconds to parse pdfs.".format(int(time()-t)))


if __name__ == "__main__":
    main()
