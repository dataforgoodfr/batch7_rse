# general imports
from pathlib import Path
import os
import re
import argparse
from time import time
import multiprocessing as mp
from functools import partial
from collections import Counter

# processing imports
import numpy as np
import pandas as pd
from tqdm import tqdm
from collections import OrderedDict
from difflib import SequenceMatcher
import os

# pdfminer imports
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTPage, LTChar, LTAnno, LAParams, LTTextBox, LTTextLine

# local imports

import rse_watch.sententizer as sententizer


def get_list_of_pdfs_filenames(dirName):
    """
        For the given path, get the List of all files in the directory tree
    """
    paths = []
    for path, subdirs, files in os.walk(dirName):
        for name in files:
            if (name.lower().endswith(".pdf")):
                paths.append((Path(path + "/" + name)))
    return paths


def get_companies_metadata_dict(config):
    """ Read companies metadata from config and turn it into dictionnary"""
    companies_metadata_dict = pd.read_csv(config.annotations_file,
                                          sep=";",
                                          encoding='utf-8-sig').set_index("project_denomination").T.to_dict()
    return companies_metadata_dict


def clean_child_str(child_str):
    child_str = ' '.join(child_str.split()).strip()
    # dealing with hyphens:
    # 1. Replace words separators in row by a different char than hyphen (i.e. longer hyphen)
    child_str = re.sub("[A-Za-z] - [A-Za-z]", lambda x: x.group(0).replace(' - ', ' – '), child_str)
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


def get_raw_content_from_pdf(input_file, rse_range=None):
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
    first_page_nb = pages_selection[0] + 1  # to start indexation at 1
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


def get_paragraphs_from_raw_content(device, idx_first_page):
    """
    From parsed data with positional information, aggregate into paragraphs using simple rationale
    :param device:
    :param idx_first_page:
    :param p: size of next gap needs to be smaller than previous min size of letters (among two last rows) times p
    :return:
    """
    # GROUPING BY COLUMN
    column_text_dict = OrderedDict()  # keep order of identification in the document.

    APPROXIMATION_FACTOR = 10  # to allow for slight shifts at beg of aligned text
    N_MOST_COMMON = 4  # e.g. nb max of columns of text that can be considered
    LEFT_SECURITY_SHIFT = 20  # to include way more shifted text of previous column
    counter = Counter()
    item_holder = []

    item_index = 0
    while "There are unchecked items in device.rows":

        # add the item to the list of the page
        (page_id, x_min, _, _, _, _) = device.rows[item_index]
        item_holder.append(device.rows[item_index])

        # increment the count of x_min
        counter[(x_min // APPROXIMATION_FACTOR) * APPROXIMATION_FACTOR] += 1

        # go to next item
        it_was_last_item = item_index == (len(device.rows) - 1)
        if not it_was_last_item:
            item_index += 1
            (next_page_id, _, _, _, _, _) = device.rows[item_index]
            changing_page = (next_page_id > page_id)

        if changing_page or it_was_last_item:  # approximate next page

            top_n_x_min_approx = counter.most_common(N_MOST_COMMON)
            df = pd.DataFrame(top_n_x_min_approx, columns=["x_min_approx", "freq"])
            df = df[df["freq"] > df["freq"].sum() * (1 / (N_MOST_COMMON + 1))].sort_values(by="x_min_approx")
            x_min_approx = (df["x_min_approx"] - LEFT_SECURITY_SHIFT).values
            x_min_approx = x_min_approx * (x_min_approx > 0)
            left_x_min_suport = np.hstack([x_min_approx,
                                           [10000]])

            def x_grouper(x_min):
                delta = left_x_min_suport - x_min
                x_group = left_x_min_suport[np.argmin(delta < 0) * 1 - 1]
                return x_group

            # iter on x_group and add items
            page_nb = idx_first_page + page_id
            column_text_dict[page_nb] = {}

            for item in item_holder:
                (page_id, x_min, y_min, x_max, y_max, text) = item
                page_nb = idx_first_page + page_id
                x_group = x_grouper(x_min)
                if x_group in column_text_dict[page_nb].keys():
                    column_text_dict[page_nb][x_group].append((y_min, y_max, text))
                else:
                    column_text_dict[page_nb][x_group] = [(y_min, y_max, text)]

            if it_was_last_item:
                break
            else:
                # restart from zero for next page
                counter = Counter()
                item_holder = []


    # CREATE THE PARAGRAPHS IN EACH COLUMN
    # define minimal conditions to define a change of paragraph:
    # Being spaced by more than the size of each line (min if different to account for titles)
    pararaphs_list = []
    paragraph_index = 0
    for page_nb, x_groups_dict in column_text_dict.items():
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

                relative_var_in_height = (current_height - previous_height) / float(
                    current_height)  # Was min before ???
                relative_var_in_y_min = abs(current_y_min - previous_y_min) / float(current_height)

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
                        # if change_in_font_size:  # to separate titles
                        #     paragraph = paragraph + ".\n"
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


def parse_paragraphs_from_pdf(input_file, rse_ranges=None):
    """
    From filename, parse pdf and output structured paragraphs with filter on rse_ranges uif present.
    :param input_file: filename ending  with ".pdf" or ".PDF".
    :param rse_ranges: "(start, end)|(start, end)"
    :return: df[[page_nb, page_text]] dataframe
    """
    rse_ranges_list = list(map(eval, rse_ranges.split("|")))
    df_paragraphs_list = []
    for rse_range in rse_ranges_list:
        df_par, idx_first_page = get_raw_content_from_pdf(input_file, rse_range=rse_range)
        df_par = get_paragraphs_from_raw_content(df_par, idx_first_page)
        df_paragraphs_list.append(df_par)
    df_par = pd.concat(df_paragraphs_list, axis=0, ignore_index=True)
    return df_par


def compute_string_similarity(a, b):
    """Compares two strings and returns a similarity ratio between 0 and 1 """
    return SequenceMatcher(None, a, b).ratio()


def cut_footer(df_par, p=0.8, verbose=False):
    """
    Cut the paragraph with lowest y_min if other paragraphs are similar.
    The similarity is measured with function compute_string_similarity
    """
    len_first = len(df_par)
    footers = []
    deno = df_par['project_denomination'].values[0]
    c = 0
    while True:
        c += 1
        len_start = len(df_par)
        y_bottom = df_par['y_min_paragraph'].min()
        y_top = df_par[df_par['y_min_paragraph'] == y_bottom]['y_max_paragraph'].min()
        DSmin = df_par[(df_par['y_max_paragraph'] == y_top) & (df_par['y_min_paragraph'] == y_bottom)].copy()
        if len(DSmin) == 1 and c == 1:
            if verbose:
                print('\n', deno)
            return df_par
        if len(DSmin) == 1:
            break
        for candidate in DSmin['paragraph'].values:
            DSmin['is_foot'] = DSmin['paragraph'].apply(lambda x: compute_string_similarity(str(x), candidate) > p)
            count = len((DSmin[DSmin['is_foot'] == True]))
            if count > 1:
                footers.append((candidate, count))
                index_foot = DSmin[DSmin['is_foot'] == True].index
                break
            else:
                DSmin = DSmin.drop(DSmin.index[0])
        if len(footers) == 0:
            if verbose:
                print('\n', deno)
            return df_par
        len_end = (len(df_par[~df_par.index.isin(index_foot)]))
        df_par = df_par[~df_par.index.isin(index_foot)]
        if len_start == len_end:
            break
    # Below part is for human check that the function works properly
    # if verbose:
    #     len_last = len(df_par)
    #     S = sum([i for _,i in footers])
    #     print('\n',deno)
    #     print(f"Removed {len_first-len_last} lines. {len_first-len_last==S}")
    #     if footers!=[]:
    #         L = [foot+" x "+ str(count) for foot, count in footers]
    #         print("Footers(s) --->\n",'\n '.join(L))
    return df_par


def cut_header(df_par, p=0.8, verbose=False):
    "Same as function cut_footer() but for headers"
    len_first = len(df_par)
    headers = []
    deno = df_par['project_denomination'].values[0]
    c = 0
    while True:
        c += 1
        len_start = len(df_par)
        y_top = df_par['y_max_paragraph'].max()
        y_bottom = df_par[df_par['y_max_paragraph'] == y_top]['y_min_paragraph'].max()
        DSmax = df_par[(df_par['y_max_paragraph'] == y_top) & (df_par['y_min_paragraph'] == y_bottom)].copy()
        if len(DSmax) == 1 and c == 1:
            if verbose:
                print('\n', deno)
            return df_par
        if len(DSmax) == 1:
            break
        for candidate in DSmax['paragraph'].values:
            DSmax['is_head'] = DSmax['paragraph'].apply(lambda x: compute_string_similarity(str(x), candidate) > p)
            count = len((DSmax[DSmax['is_head'] == True]))
            if count > 1:
                headers.append((candidate, count))
                index_head = DSmax[DSmax['is_head'] == True].index
                break
            else:
                DSmax = DSmax.drop(DSmax.index[0])
        if len(headers) == 0:
            if verbose:
                print('\n', deno)
            return df_par
        len_end = (len(df_par[~df_par.index.isin(index_head)]))
        df_par = df_par[~df_par.index.isin(index_head)]
        if len_start == len_end:
            break

    # Below part is for human check that the function works properly
    # if verbose:
    #     len_last = len(df_par)
    #     S = sum([i for _, i in headers])
    #     print('\n', deno)
    #     print(f"Removed {len_first - len_last} lines. {len_first - len_last == S}")
    #     if headers != []:
    #         L = [head + " x " + str(count) for head, count in headers]
    #         print("Header(s) --->\n", '\n '.join(L))

    return df_par


def get_paragraphs_dataframe_from_pdf(dpef_path, dict_annotations):
    """
    Parse a pdf and return a pandas df with paragraph level parsed text.

    :param dpef_path_dict_annotations: (inpout_file, dict_annotations) tuple
    :return:
    """
    project_denomination = dpef_path.name.split("_")[0]
    company_sector = dpef_path.parent.name
    document_year = dpef_path.name.split("_")[1]
    t = time()
    print("Start for {} [{}]".format(
        project_denomination,
        dpef_path.name)
    )
    try:
        rse_ranges = dict_annotations[project_denomination]["rse_ranges_"+document_year]
    except KeyError:
        print("RSE ranges not found for company {} for year {}".format(project_denomination,
                                                                       document_year))
    df_par = parse_paragraphs_from_pdf(dpef_path, rse_ranges=rse_ranges)
    df_par.insert(0, "project_denomination", project_denomination)
    df_par.insert(1, "company_sector", company_sector)
    df_par.insert(2, "document_year", document_year)
    df_par = df_par.drop_duplicates(['paragraph'])
    df_par = cut_footer(df_par, verbose=True)
    df_par = cut_header(df_par, verbose=True)

    print("End for {} [{}] - took {} seconds".format(
        project_denomination,
        dpef_path.name,
        int(t - time()))
    )
    return df_par


def get_sentences_dataframe_from_pdf(config, dpef_path):
    """ Parse a pdf and return a pandas df with sentence level parsed text"""
    companies_metadata_dict = get_companies_metadata_dict(config)
    df_par = get_paragraphs_dataframe_from_pdf(dpef_path, companies_metadata_dict)
    df_sent = sententizer.get_sentence_dataframe_from_paragraph_dataframe(df_par, config)
    return df_sent


def get_sentences_from_all_pdfs(config):
    """
    Parses all dpefs into a sentence-level format and save the resulting csv according to config.
    """
    companies_metadata_dict = get_companies_metadata_dict(config)
    all_input_files = get_list_of_pdfs_filenames(config.dpef_dir)
    all_input_files = [input_file for input_file in all_input_files if
                       input_file.name.split("_")[0] in companies_metadata_dict.keys()]

    # PARALLELIZATION
    parallel_get_sentences_dataframe_from_pdf = partial(get_sentences_dataframe_from_pdf,
                                                        config)
    n_cores = mp.cpu_count() - 1 or 1

    with mp.Pool(n_cores) as pool:
        print("Multiprocessing with {} cores".format(n_cores))
        df_sents = list(
            tqdm(
                pool.imap(
                    parallel_get_sentences_dataframe_from_pdf,
                    all_input_files
                ),
                total=len(all_input_files)
            )
        )

    # concat
    df_sents = pd.concat(df_sents, axis=0, ignore_index=True)
    # create parent folder
    pickle_path = config.parsed_sent_file.parent
    pickle_path.mkdir(parents=True, exist_ok=True)
    # save to csv
    df_sents.to_csv(config.parsed_sent_file, sep=";", index=False, encoding='utf-8-sig')

    return df_sents


def run(config):
    """
    Parse the pdfs into structured csv formats (for now)
    : param conf: conf object with relative paths.
    :param task: "parser", "sententizer" or "both" ; Whether to parse
    pdfs, sententize the paragraphs, or do both.
    """
    df_sents = get_sentences_from_all_pdfs(config)
    print(df_sents.shape)
    return df_sents
