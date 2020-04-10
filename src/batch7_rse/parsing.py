# general imports
from pathlib import Path
import os
import argparse
from time import time
import multiprocessing as mp

# processing imports
import pandas as pd
import numpy as np
from tqdm import tqdm
from collections import OrderedDict

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


def pdf_to_raw_content(input_file, rse_range=None):
    """
    Parse pdf file,  within rse range of pages if needed, and return list of rows with all metadata
    :param input_file: PDF filename
    :param rse_range: (nb_first_page_rse:int, nb_last_page_rse:int) tuple, starting at 1
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

    if rse_range is not None and rse_range != "":
        # start at zero to match real index of pages
        pages_selection = range(rse_range[0] - 1, (rse_range[1] - 1) + 1)
    else:
        pages_selection = range(0, 10000)
    first_page_nb = pages_selection[0]+1  # to start indexation at 1
    for nb_page_parsed, page in enumerate(PDFPage.create_pages(doc)):
        if nb_page_parsed in pages_selection:
            interpreter.process_page(page)
            device.get_result()

    return device, first_page_nb


def raw_content_to_paragraphs(device, idx_first_page, wiggle_room = 1):
    """
    From parsed data with positional information, aggregate into paragraphs using simple rationale
    :param device:
    :param idx_first_page:
    :param p: size of next gap needs to be smaller than previous min size of letters (among two last rows) times p
    :return:
    """
    # GROUPING BY COLUMN
    column_text = OrderedDict()  # keep order of identification in the document.
    for (page_nb, x_min, y_min, _, y_max, text) in device.rows:
        page_nb = idx_first_page + page_nb  # elsewise device starts again at 0
        if page_nb not in column_text.keys():
            column_text[page_nb] = {}
        x_group = round(x_min) // 150  # Si trois paragraphes -> shift de 170, max à droite ~600 # problem was shifted titles
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
                min_height = max(previous_height, current_height)
                relative_var_in_height = abs(current_height-previous_height)/float(min_height)
                # or (p["y_min"] - y_max) > min_height*wiggle_room
                if relative_var_in_height > 0.08:
                    # break paragraph, start new one
                    x_groups_data_paragraphs.append(p)
                    p = {"y_min": y_min,
                         "y_max": y_max,
                         "paragraph": paragraph}
                else:
                    # paragraph continues
                    p["y_min"] = y_min
                    p["paragraph"] = p["paragraph"] + " " + paragraph

                previous_height = current_height
            # add the last paragraph of column
            x_groups_data_paragraphs.append(p)
            # structure the output
            for p in x_groups_data_paragraphs:
                pararaphs_list.append({"paragraph_id": paragraph_index,
                                           "page_nb": page_nb,
                                           "x_group": x_group_name,
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


def pdf_to_pages(input_file):
    """
    From filename, parse pdf and output structured text. possible filter on rse_ranges
    :param input_file: filename ending  with ".pdf" or ".PDF".
    :param rse_ranges: "(start, end)|(start, end)"
    :return: df[[page_nb, page_text]] dataframe
    """
    raw_content, idx_first_page = pdf_to_raw_content(input_file, rse_range=None) # ALWAYS NONE for pages
    df_paragraphs = raw_content_to_paragraphs(raw_content, idx_first_page)
    df_by_page = paragraphs_to_pages(df_paragraphs)
    return df_by_page


def pdf_to_paragraphs(input_file, rse_ranges=None):
    """
    From filename, parse pdf and output structured paragraphs with filter on rse_ranges uif present.
    :param input_file: filename ending  with ".pdf" or ".PDF".
    :param rse_ranges: "(start, end)|(start, end)"
    :return: df[[page_nb, page_text]] dataframe
    """
    rse_ranges_list = list(map(eval, rse_ranges.split("|")))
    df_paragraphs_list = []
    for rse_range in rse_ranges_list:
        raw_content, idx_first_page = pdf_to_raw_content(input_file, rse_range=rse_range)
        df_paragraphs = raw_content_to_paragraphs(raw_content, idx_first_page)
        df_paragraphs_list.append(df_paragraphs)
    df_paragraphs = pd.concat(df_paragraphs_list, axis=0, ignore_index=True)
    return df_paragraphs


#### TRANSFORMATIONS


def get_annotated_pages(input_file_dict_annotations):
    input_file, dict_annotations = input_file_dict_annotations
    project_denomination = input_file.name.split("_")[0]
    rse_ranges = dict_annotations[project_denomination]["rse_ranges"]
    t = time()
    print("Start for {} [{}] - RSE pages are {}".format(
        project_denomination,
        input_file.name),
        rse_ranges
    )

    annotated_pages_df = pdf_to_pages(input_file, rse_ranges=None) # none so all are taken
    annotated_pages_df["project_denomination"] = project_denomination
    annotated_pages_df["rse_label"] = 0
    rse_ranges_list = list(map(eval, rse_ranges.split("|")))
    for rse_ranges in rse_ranges_list:
        annotated_pages_df.loc[annotated_pages_df["page_nb"].between(rse_ranges[0], rse_ranges[1]), "rse_label"] = 1

    print("          End for {} [{}] - took {} seconds".format(
        project_denomination,
        input_file.name,
        round(t-time()))
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
    pages_df["rse_label"] = np.nan

    print("\n End for {} [{}] - took {} seconds".format(
        project_denomination,
        input_file.name,
        t-time())
    )
    return pages_df


def get_final_paragraphs(input_file_dict_annotations):
    """
    Get paragraphs from pdf of one DPEF.
    :param input_file_dict_annotations: (inpout_file, dict_annotations) tuple
    :return:
    """
    input_file, dict_annotations = input_file_dict_annotations
    project_denomination = input_file.name.split("_")[0]
    t = time()
    print("Start for {} [{}]".format(
        project_denomination,
        input_file.name)
    )
    rse_ranges = dict_annotations[project_denomination]["rse_ranges"]
    paragraphs_df = pdf_to_paragraphs(input_file, rse_ranges=rse_ranges)
    paragraphs_df.insert(0, "project_denomination", project_denomination)

    print("          End for {} [{}] - took {} seconds".format(
        project_denomination,
        input_file.name,
        t-time())
    )
    return paragraphs_df


def create_labeled_data(annotations_filename="../../data/input/Entreprises/entreprises_rse_annotations.csv",
                        input_path="../../data/input/DPEFs/",
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
    all_input_files = all_input_files[-3:]
    # all_input_files = [input_file for input_file in all_input_files if input_file.name.split("_")[0] not in dict_annotations.keys()]

    n_cores = mp.cpu_count()-1 or 1  # use all cores except one
    pool = mp.Pool(n_cores)
    print("Multiprocessing with {} cores".format(n_cores))
    annotated_dfs = list(tqdm(pool.imap(get_unlabeled_pages, all_input_files), total=len(all_input_files)))

    # concat
    annotated_dfs = pd.concat(annotated_dfs, axis=0, ignore_index=True)
    annotated_dfs = annotated_dfs[["project_denomination", "page_nb", "page_text", "rse_label"]]
    annotated_dfs.to_csv(output_filename, sep=";", index=False)
    return annotated_dfs


# TODO: change annotation to the final annotation file !
# TODO : create a unique, stable ID for all paragraps
def create_final_dataset(annotations_filename="../../data/input/Entreprises/entreprises_rse_annotations.csv",
                         input_path="../../data/input/DPEFs/",
                         output_filename="../../data/processed/DPEFs/dpef_paragraphs.csv"):
    """
    Create structured paragraphs from dpef, using only rse sections.
    :param annotations_filename: path to denomination - rse_range mapping
    :param input_path: path to folder of DPEF pdfs
    :param output_filename: path to output csv
    """
    dict_annotations = pd.read_csv(annotations_filename, sep=";").set_index("project_denomination").T.to_dict()
    all_input_files = get_list_of_pdfs_filenames(input_path, only_pdfs=True)
    all_input_files = [input_file for input_file in all_input_files if input_file.name.split("_")[0] in dict_annotations.keys()]
    input_data = list(zip(all_input_files, [dict_annotations]*len(all_input_files))) # TODO change
    n_cores = mp.cpu_count()-1 or 1
    pool = mp.Pool(n_cores) # use all
    print("Multiprocessing with {} cores".format(n_cores))
    paragraphs_df = list(tqdm(pool.imap(get_final_paragraphs, input_data), total=len(all_input_files)))
    # TO DEBUG USE: annotated_dfs = [get_final_paragraphs(input_data[0])]

    # concat
    paragraphs_df = pd.concat(paragraphs_df, axis=0, ignore_index=True)
    paragraphs_df.to_csv(output_filename, sep=";", index=False)

    return paragraphs_df


if __name__ == "__main__":
    # execute only if run as a script
    parser = argparse.ArgumentParser()

    parser.add_argument('--task',
                        default="train",
                        choices=["train","unlabeled","final"],
                        help='Create labeled pages, parse all unlabeled pages, or do final paragraph/sentence parsing')

    args = parser.parse_args()
    if args.task == "train":

        # a conf file could be read, else use default filenames
        # Took 11 minutes.
        print("Create training data for recognizing rse pages in DPEF.")
        create_labeled_data()
        print("Over")

    elif args.task == "unlabeled":

        print("Create unlabeled data for recognizing rse pages in DPEF.")
        create_unlabeled_dataset()
        print("Over")

    elif args.task == "final":

        # use function with similar structure as make_train, but keep paragraphs this time.
        # Split into sentences can be separated in another script
        print("Create final data structured as paragraphs from rse sections in DPEF.")
        create_final_dataset()
        print("Over")