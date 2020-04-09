# general imports
from pathlib import Path
import os
import sys, argparse
from time import time

# processing imports
import pandas as pd
from tqdm import tqdm
from collections import OrderedDict
import multiprocessing as mp

# pdfminer imports
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTPage, LTChar, LTAnno, LAParams, LTTextBox, LTTextLine
# from difflib import SequenceMatcher

N_PROCESSES = -1


def get_list_of_pdfs_filenames(dirName, only_pdfs = True):
    '''
        For the given path, get the List of all files in the directory tree
    '''
    paths = []
    for path, subdirs, files in os.walk(dirName):
        for name in files:
            if (name.lower().endswith(".pdf")) or not only_pdfs:
                paths.append((Path(path+"/"+name)))
    return paths


class PDFPageDetailedAggregator(PDFPageAggregator):
    """
    Custom class to parse pdf and keep position of parsed text lines.
    """

    def __init__(self, rsrcmgr, pageno=1, laparams=None):
        PDFPageAggregator.__init__(self, rsrcmgr, pageno=pageno, laparams=laparams)
        self.rows = []
        self.page_number = 0
        self.result = ""

    def receive_layout(self, ltpage):
        def render(item, page_number):
            if isinstance(item, LTPage) or isinstance(item, LTTextBox):
                for child in item:
                    render(child, page_number)
            elif isinstance(item, LTTextLine):
                child_str = ''
                for child in item:
                    if isinstance(child, (LTChar, LTAnno)):
                        child_str += child.get_text()
                child_str = ' '.join(child_str.split()).strip()
                if child_str:
                    # bbox == (pagenb, x1, y1, x2, y2, text)
                    row = (page_number, item.bbox[0], item.bbox[1], item.bbox[2], item.bbox[3], child_str)
                    self.rows.append(row)
                for child in item:
                    render(child, page_number)
            return

        render(ltpage, self.page_number)
        self.page_number += 1
        self.rows = sorted(self.rows, key=lambda x: (x[0], -x[2]))
        self.result = ltpage


def pdf_to_raw_content(input_file, rse_ranges=None):
    """
    Parse pdf file,  within rse range of pages if needed, and return list of rows with all metadata
    :param input_file: PDF filename
    :param rse_ranges: (nb_first_page_rse:int, nb_last_page_rse:int), starting at 1
    :return: list of rows with (pagenb, x1, y1, x2, y2, text) and page_nb starts at 0!
    """
    assert input_file.name.endswith(".pdf")
    fp = open(input_file, 'rb')

    parser = PDFParser(fp)
    doc = PDFDocument(parser)
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageDetailedAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    if rse_ranges is not None:
        # start at zero to match real index of pages
        pages_selection = range(rse_ranges[0] - 1, (rse_ranges[1] - 1) + 1)
    else:
        pages_selection = range(0, 10000)
    first_page_nb = pages_selection[0]+1  # to start indexation at 1
    for nb_page_parsed, page in enumerate(PDFPage.create_pages(doc)):
        if nb_page_parsed in pages_selection:
            interpreter.process_page(page)
            device.get_result()

    return device, first_page_nb


def raw_content_to_paragraphs(device, idx_first_page):
    # GROUPING BY COLUMN
    column_text = OrderedDict()  # keep order of identification in the document.
    for (page_nb, x_min, y_min, _, y_max, text) in device.rows:
        page_nb = idx_first_page + page_nb  # elsewise device starts again at 0
        if page_nb not in column_text.keys():
            column_text[page_nb] = {}
        x_group = round(x_min) // 50  # Si trois paragraphes -> shift de 170, max à droite ~600 # TODO: decrease, no groups are created here !
        if x_group in column_text[page_nb].keys():
            column_text[page_nb][x_group].append((y_min, y_max, text))
        else:
            column_text[page_nb][x_group] = [(y_min, y_max, text)]

    pararaphs_list = []
    paragraph_index = 0

    # CREATE THE PARAGRAPHS IN EACH COLUMN
    # define minimal conditions to define a change of paragraph:
    # Being spaced by more than the size of each line (min if different to account for titles)
    for page_nb, x_groups_dict in column_text.items():
        for x_group_name, x_groups_data in x_groups_dict.items():
            x_groups_data = sorted(x_groups_data, key=lambda x: x[0],
                                   reverse=True)  # sort vertically, higher y = before
            x_groups_data_paragraphs = []

            p = {"y_min": x_groups_data[0][0],
                 "y_max": x_groups_data[0][1],
                 "paragraph": x_groups_data[0][2]}
            previous_height = p["y_max"] - p["y_min"]
            for y_min, y_max, paragraph in x_groups_data[1:]:
                current_height = y_max - y_min
                min_height = min(previous_height, current_height)

                if (p["y_min"] - y_max) < min_height:  # paragraph update
                    p["y_min"] = y_min
                    p["paragraph"] = p["paragraph"] + " " + paragraph
                else:  # break paragraph, start new one
                    x_groups_data_paragraphs.append(p)
                    p = {"y_min": y_min,
                         "y_max": y_max,
                         "paragraph": paragraph}
                previous_height = current_height
            # add the last paragraph of column
            x_groups_data_paragraphs.append(p)
            # structure the output
            for p in x_groups_data_paragraphs:
                pararaphs_list.append({"paragraph_id": paragraph_index,
                                           "page_nb": page_nb,
                                           "x_group": x_group,
                                           "y_min_paragraph": round(p["y_min"]),
                                           "y_max_paragraph": round(p["y_max"]),
                                           "paragraph": p["paragraph"]})
                paragraph_index += 1
    df_paragraphs = pd.DataFrame(data=pararaphs_list,
                                  columns=["paragraph_id",
                                           "page_nb",
                                           "paragraph",
                                           "x_group",
                                           "y_min_paragraph",
                                           "y_max_paragraph"])
    return df_paragraphs

def paragraphs_to_pages(df_paragraphs):
    """

    :param df_paragraphs: df with paragraphs sorted by paragraph id
    :return: df with one text by page
    """
    # TODO: be sure that the text is cleaned before using ?
    df_by_page = df_paragraphs.sort_values(["page_nb", "paragraph_id"])
    df_by_page = df_by_page.groupby("page_nb")["paragraph"].apply(lambda x: "\n".join(x))
    df_by_page = df_by_page.reset_index()
    df_by_page = df_by_page.rename(columns={"paragraph":"page_text"})
    return df_by_page


def pdf_to_pages(input_file, rse_ranges=None):
    """
    From filename, parse pdf and output structured text. possible filter on rse_ranges
    :param input_file: filename ending  with ".pdf" or ".PDF".
    :param rse_ranges: "(start, end)|(start, end)"
    :return: df[[page_nb, page_text]] dataframe
    """
    raw_content, idx_first_page = pdf_to_raw_content(input_file, rse_ranges=rse_ranges)
    df_paragraphs = raw_content_to_paragraphs(raw_content, idx_first_page)
    df_by_page = paragraphs_to_pages(df_paragraphs)
    return df_by_page


#### TRANSFORMATIONS


def get_annotated_pages(input_file_dict_annotations):
    input_file, dict_annotations = input_file_dict_annotations
    project_denomination = input_file.name.split("_")[0]
    t = time()
    print("Start for {} [{}]".format(
        project_denomination,
        input_file.name)
    )

    annotated_pages_df = pdf_to_pages(input_file, rse_ranges=None) # none so all are taken
    annotated_pages_df["project_denomination"] = project_denomination
    annotated_pages_df["rse_label"] = 0
    rse_ranges_list = list(map(eval, dict_annotations[project_denomination]["rse_ranges"].split("|")))
    for rse_ranges in rse_ranges_list:
        annotated_pages_df.loc[annotated_pages_df["page_nb"].between(rse_ranges[0], rse_ranges[1]), "rse_label"] = 1

    print("          End for {} [{}] - took {} seconds".format(
        project_denomination,
        input_file.name,
        t-time())
    )
    return annotated_pages_df


def get_unlabeled_pages(input_file):

    project_denomination = input_file.name.split("_")[0]
    t = time()
    print("\n Start for {} [{}]".format(
        project_denomination,
        input_file.name)
    )
    pages_df = pdf_to_pages(input_file, rse_ranges=None)
    pages_df["project_denomination"] = project_denomination
    pages_df["rse_label"] = 0

    print("\n End for {} [{}] - took {} seconds".format(
        project_denomination,
        input_file.name,
        t-time())
    )
    return pages_df


def create_labeled_data(annotations_filename="../../data/input/Entreprises/entreprises_rse_annotations.csv",
                        input_path="../../data/input/DPEFs/",  # TODO change luxe is smaller subset
                        output_filename="../../data/processed/DPEFs/dpef_rse_pages_train.csv"):
    """
    From a list of rse ranges of pages and the repo of all dpef, create a training dataset with all labelled pages.
    :param annotations_filename:
    :param input_path:
    :param output_filename:
    :return:
    """
    dict_annotations = pd.read_csv(annotations_filename, sep=";").set_index("project_denomination").T.to_dict()
    all_input_files = get_list_of_pdfs_filenames(input_path, only_pdfs=True)
    all_input_files = [input_file for input_file in all_input_files if input_file.name.split("_")[0] in dict_annotations.keys()]
    input_data = list(zip(all_input_files, [dict_annotations]*len(all_input_files)))
    n_cores = mp.cpu_count()-1 or 1
    pool = mp.Pool(n_cores) # use all
    print("Multiprocessing with {} cores".format(n_cores))
    annotated_dfs = list(tqdm(pool.imap(get_annotated_pages, input_data), total=len(all_input_files)))
    # TO DEBUG USE:
    # annotated_dfs = [get_annotated_df(input_data[0])]

    # concat
    annotated_dfs = pd.concat(annotated_dfs, axis=0, ignore_index=True)
    annotated_dfs = annotated_dfs[["project_denomination", "page_nb", "page_text", "rse_label"]]
    annotated_dfs.to_csv(output_filename, sep=";", index=False)
    return annotated_dfs


def create_unlabeled_dataset(annotations_filename="../../data/input/Entreprises/entreprises_rse_annotations.csv",
                            input_path="../../data/input/DPEFs/",
                            output_filename="../../data/processed/DPEFs/dpef_unlabeld_pages.csv"):
    """
    From a list of rse ranges of pages and the repo of all dpef, create a training dataset with all labelled pages.
    :param annotations_filename:
    :param input_path:
    :param output_filename:
    :return:
    """
    dict_annotations = pd.read_csv(annotations_filename, sep=";").set_index("project_denomination").T.to_dict()
    all_input_files = get_list_of_pdfs_filenames(input_path, only_pdfs=True)
    # here the "not" is key to get unlabeled elements only
    # TODO: uncomment when more data available
    all_input_files = all_input_files[-2:]
    # all_input_files = [input_file for input_file in all_input_files if input_file.name.split("_")[0] not in dict_annotations.keys()]

    n_cores = mp.cpu_count()-1 or 1
    pool = mp.Pool(n_cores) # use all
    print("Multiprocessing with {} cores".format(n_cores))
    annotated_dfs = list(tqdm(pool.imap(get_unlabeled_pages, all_input_files), total=len(all_input_files)))

    # concat
    annotated_dfs = pd.concat(annotated_dfs, axis=0, ignore_index=True)
    annotated_dfs = annotated_dfs[["project_denomination", "page_nb", "page_text", "rse_label"]]
    annotated_dfs.to_csv(output_filename, sep=";", index=False)
    return annotated_dfs


def make_train_data():
    # a conf file could be read, else use default filenames
    # Took 11 minutes.
    print("Create training data for recognizing rse pages in DPEF.")
    create_labeled_data()
    print("Over")


def make_unlabeled_data():
    print("Create unlabeled data for recognizing rse pages in DPEF.")
    create_unlabeled_dataset()
    print("Over")

def make_final_data():
    # use function with similar structure as make_train, but keep paragraphs this time.
    pass

if __name__ == "__main__":
    # execute only if run as a script
    parser = argparse.ArgumentParser()

    parser.add_argument('--task',
                        default="train",
                        choice=["train","unlabeled","final"],
                        help='Create labeled pages, parse all unlabeled pages, or do final paragraph/sentence parsing')

    args = parser.parse_args()
    if args.task == "train":
        make_train_data()
    elif args.task == "unlabeled":
        make_unlabeled_data()
    elif args.task == "final":
        make_final_data()
