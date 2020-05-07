# general imports
from pathlib import Path
import os
import re
import argparse
from time import time
import multiprocessing as mp

# processing imports
import pandas as pd
from tqdm import tqdm
from collections import OrderedDict
from difflib import SequenceMatcher

# pdfminer imports
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTPage, LTChar, LTAnno, LAParams, LTTextBox, LTTextLine

# local imports
import sententizer
from conf import *

def get_list_of_pdfs_filenames(dirName):
    """
        For the given path, get the List of all files in the directory tree
    """
    paths = []
    for path, subdirs, files in os.walk(dirName):
        for name in files:
            if (name.lower().endswith(".pdf")):
                paths.append((Path(path+"/"+name)))
    return paths


def clean_child_str(child_str):
    child_str = ' '.join(child_str.split()).strip()
    # dealing with hyphens:
    # 1. Replace words separators in row by a different char than hyphen (i.e. longer hyphen)
    child_str = re.sub("[A-Za-z] - [A-Za-z]", lambda x:x.group(0).replace(' - ', ' – '), child_str)
    # 2. Attach the negative term to the following number, # TODO: inutile ? Enlever ?
    child_str = re.sub("(- )([0-9])", r"-\2", child_str)
    return child_str


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
                child_str = clean_child_str(child_str)
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
    # Checked: only useful pages are actually parsed.
    for nb_page_parsed, page in enumerate(PDFPage.create_pages(doc)):
        if nb_page_parsed in pages_selection:
            interpreter.process_page(page)
            device.get_result()

    return device, first_page_nb


def clean_paragraph(p):
    """ Curate paragraph object before save, in particular deal with hyphen and spaces """
    # Attach together words (>= 2 char to avoid things like A minus, B minus...)
    # that may have been split at end of row like géographie = "géo - graphie"
    # real separator have been turned into longer hyphen during parsing to avoid confusion with those.
    # Accents accepted thks to https://stackoverflow.com/a/24676780/8086033
    w_expr = "(?i)(?:(?![×Þß÷þø])[-'a-zÀ-ÿ]){2,}"
    p["paragraph"] = re.sub("{} - {}".format(w_expr, w_expr),
                            lambda x: x.group(0).replace(' - ', ''),
                            p["paragraph"])
    # reattach words that were split, like Fort-Cros = "Fort- Cros"
    p["paragraph"] = re.sub("{}- {}".format(w_expr, w_expr),
                            lambda x: x.group(0).replace('- ', '-'),
                            p["paragraph"])
    return p


def raw_content_to_paragraphs(device, idx_first_page):
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
            previous_y_min = p["y_min"]
            for y_min, y_max, paragraph in x_groups_data[1:]:
                current_height = y_max - y_min
                current_y_min = y_min
                max_height = max(previous_height, current_height)

                relative_var_in_height = (current_height-previous_height)/float(max_height)  # Was min before ???
                relative_var_in_y_min = abs(current_y_min-previous_y_min)/float(current_height)

                positive_change_in_font_size = (relative_var_in_height > 0.05)
                change_in_font_size = abs(relative_var_in_height) > 0.05
                different_row = (relative_var_in_y_min > 0.7)
                large_gap = (relative_var_in_y_min > 1.2)
                artefact_to_ignore = (len(paragraph) <= 2)  # single "P" broke row parsing in auchan dpef
                if not artefact_to_ignore:
                    if (positive_change_in_font_size and different_row) or large_gap:  # always break
                        # break paragraph, start new one
                        # print("break",relative_var_in_height, relative_var_in_y_min, paragraph)
                        p = clean_paragraph(p)
                        x_groups_data_paragraphs.append(p)
                        p = {"y_min": y_min,
                             "y_max": y_max,
                             "paragraph": paragraph}
                    else:
                        if change_in_font_size:  # to separate titles
                            paragraph = paragraph + ".\n"
                        # paragraph continues
                        p["y_min"] = y_min
                        p["paragraph"] = p["paragraph"] + " " + paragraph

                    previous_height = current_height
                    previous_y_min = current_y_min
            # add the last paragraph of column
            p = clean_paragraph(p)
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
    df_par = pd.DataFrame(data=pararaphs_list,
                                  columns=["paragraph_id",
                                           "page_nb",
                                           "paragraph",
                                           "x_group",
                                           "y_min_paragraph",
                                           "y_max_paragraph"])
    return df_par


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
        df_par, idx_first_page = pdf_to_raw_content(input_file, rse_range=rse_range)
        df_par = raw_content_to_paragraphs(df_par, idx_first_page)
        df_paragraphs_list.append(df_par)
    df_par = pd.concat(df_paragraphs_list, axis=0, ignore_index=True)
    return df_par


def compute_string_similarity(a, b):
    "Compares two strings and returns a similarity ratio between 0 and 1"
    return SequenceMatcher(None, a, b).ratio()


def cut_footer(df_par, p=0.8, verbose=False):
    "Cut the paragraph with lowest y_min if other paragraphs are similar"
    "The similarity is measured with function compute_string_similarity"
    len_first=len(df_par)
    footers=[]
    deno = df_par['project_denomination'].values[0]
    c = 0
    while True:
        c += 1
        len_start=len(df_par)
        y_bottom = df_par['y_min_paragraph'].min()
        y_top = df_par[df_par['y_min_paragraph']==y_bottom]['y_max_paragraph'].min()
        DSmin = df_par[(df_par['y_max_paragraph']==y_top)&(df_par['y_min_paragraph']==y_bottom)].copy()
        if len(DSmin)==1 and c==1:
            if verbose==True:
                print('\n',deno)
            return df_par
        if len(DSmin)==1:
            break
        for candidate in DSmin['paragraph'].values:
            DSmin['is_foot']=DSmin['paragraph'].apply(lambda x: compute_string_similarity(str(x),candidate)>p)
            count = len((DSmin[DSmin['is_foot']==True]))
            if  count>1:
                footers.append((candidate, count))
                index_foot = DSmin[DSmin['is_foot']==True].index
                break
            else:
                DSmin = DSmin.drop(DSmin.index[0])
        if len(footers)==0:
            if verbose==True:
                print('\n',deno)
            return df_par
        len_end = (len(df_par[~df_par.index.isin(index_foot)]))
        df_par = df_par[~df_par.index.isin(index_foot)]
        if len_start==len_end:
            break
    #Below part is for human check that the function works properly
    if verbose==True:
        len_last = len(df_par)
        S = sum([i for _,i in footers])
        print('\n',deno)
        print(f"Removed {len_first-len_last} lines. {len_first-len_last==S}")
        if footers!=[]:
            L = [foot+" x "+ str(count) for foot, count in footers]
            print("Footers(s) --->\n",'\n '.join(L))
    return df_par


def cut_header(df_par, p=0.8, verbose=False):
    "Same as function cut_footer() but for headers"
    len_first=len(df_par)
    headers=[]
    deno = df_par['project_denomination'].values[0]
    c=0
    while True:
        c +=1
        len_start=len(df_par)
        y_top = df_par['y_max_paragraph'].max()
        y_bottom = df_par[df_par['y_max_paragraph']==y_top]['y_min_paragraph'].max()
        DSmax = df_par[(df_par['y_max_paragraph']==y_top)&(df_par['y_min_paragraph']==y_bottom)].copy()
        if len(DSmax)==1 and c==1:
            if verbose==True:
                print('\n',deno)
            return df_par
        if len(DSmax)==1:
            break
        for candidate in DSmax['paragraph'].values:
            DSmax['is_head']=DSmax['paragraph'].apply(lambda x: compute_string_similarity(str(x),candidate)>p)
            count = len((DSmax[DSmax['is_head']==True]))
            if  count>1:
                headers.append((candidate, count))
                index_head = DSmax[DSmax['is_head']==True].index
                break
            else:
                DSmax = DSmax.drop(DSmax.index[0])
        if len(headers)==0:
            if verbose==True:
                print('\n',deno)
            return df_par
        len_end = (len(df_par[~df_par.index.isin(index_head)]))
        df_par = df_par[~df_par.index.isin(index_head)]
        if len_start==len_end:
            break

    # Below part is for human check that the function works properly
    if verbose==True:
        len_last = len(df_par)
        S = sum([i for _,i in headers])
        print('\n',deno)
        print(f"Removed {len_first-len_last} lines. {len_first-len_last==S}")
        if headers!=[]:
            L = [head+" x "+ str(count) for head, count in headers]
            print("Header(s) --->\n",'\n '.join(L))
    return df_par


# TRANSFORMATIONS PDF to TEXT

def get_final_paragraphs(input_file_dict_annotations):
    """
    Get paragraphs from pdf of one DPEF.
    :param input_file_dict_annotations: (inpout_file, dict_annotations) tuple
    :return:
    """
    input_file, dict_annotations = input_file_dict_annotations
    project_denomination = input_file.name.split("_")[0]
    company_sector = input_file.parent.name
    document_year = input_file.name.split("_")[1]
    t = time()
    print("Start for {} [{}]".format(
        project_denomination,
        input_file.name)
    )
    rse_ranges = dict_annotations[project_denomination]["rse_ranges"]
    df_par = pdf_to_paragraphs(input_file, rse_ranges=rse_ranges)
    df_par.insert(0, "project_denomination", project_denomination)
    df_par.insert(1, "company_sector", company_sector)
    df_par.insert(2, "document_year", document_year)
    df_par = df_par.drop_duplicates(['paragraph'])
    df_par = cut_footer(df_par, verbose=True)
    df_par = cut_header(df_par, verbose=True)

    print("          End for {} [{}] - took {} seconds".format(
        project_denomination,
        input_file.name,
        t-time())
    )
    return df_par


def parse_dpefs_paragraphs_into_a_dataset(conf):
    """
    Create structured paragraphs from dpef, using only rse sections.
    :param annotations_filename: path to denomination - rse_range mapping
    :param input_path: path to folder of DPEF pdfs
    :param output_filename: path to output csv
    """
    dict_annotations = pd.read_csv(conf.annotations_file, sep=";").set_index("project_denomination").T.to_dict()
    all_input_files = get_list_of_pdfs_filenames(conf.dpef_dir)
    all_input_files = [input_file for input_file in all_input_files if input_file.name.split("_")[0] in dict_annotations.keys()]
    input_data = list(zip(all_input_files, [dict_annotations]*len(all_input_files)))  # TODO change (?)
    n_cores = mp.cpu_count()-1 or 1   # use all except one if more than one available
    pool = mp.Pool(n_cores)
    print("Multiprocessing with {} cores".format(n_cores))
    paragraphs_df = list(tqdm(pool.imap(get_final_paragraphs, input_data), total=len(all_input_files)))
    # TO DEBUG USE: annotated_dfs = [get_final_paragraphs(input_data[0])]

    # concat
    paragraphs_df = pd.concat(paragraphs_df, axis=0, ignore_index=True)
    paragraphs_df.to_csv(conf.parsed_par_file, sep=";", index=False)

    return paragraphs_df


if __name__ == "__main__":
    # execute only if run as a script
    parser = argparse.ArgumentParser()

    parser.add_argument('--mode',
                        default="final",
                        choices=["final", "debug"],
                        help="Wether to parse all dpefs only a subset.")
    parser.add_argument("--task",
                        default="both",
                        choices=["parser", "sententizer","both"],
                        help="Whether to parse pdfs, sententize the paragraphs, or do both.")
    args = parser.parse_args()

    print(args)
    if args.mode == "final":
        if args.task in ["parser", "both"]:
            print("Parse paragraph level text from rse sections in DPEF.")
            parse_dpefs_paragraphs_into_a_dataset(Config)
            print("Over")
        if args.task in ["sententizer", "both"]:
            print("Sententize sentences from paragraphs of rse sections in DPEF.")
            sententizer.turn_paragraphs_into_sentences(Config)
            print("Over")

    elif args.mode == "debug":
        if args.task in ["parser", "both"]:
            print("Parse paragraph level text from rse sections in DPEF.")
            parse_dpefs_paragraphs_into_a_dataset(DebugConfig)
            print("Over")
        if args.task in ["sententizer", "both"]:
            print("Sententize sentences from paragraphs of rse sections in DPEF.")
            sententizer.turn_paragraphs_into_sentences(DebugConfig)
            print("Over")
