from webapp.polls.rse_model.rse_watch.pdf_parser import run as run_parser
from webapp.polls.rse_model.rse_watch.indexer import run as run_indexer
from webapp.conf import Config, DebugConfig
from time import time
import argparse


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--mode',
                        default="final",
                        choices=["final", "debug"],
                        help="Wether to parse all dpefs only a subset.")
    args = parser.parse_args()
    if args.mode == "final":
        config = Config
    elif args.mode == "debug":
        config = DebugConfig
    t = time()

    print("Parsing and creating NLP scorer and vectorizer.")
    run_parser(config, task="both")
    run_indexer(config)

    print("Finished intialization")
    print("Took {} seconds to parse pdfs.".format(int(time()-t)))


if __name__ == "__main__":
    main()
