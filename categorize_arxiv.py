"""
Scipt to categorise arxiv .tex files. 
Gives the source folder location, associated pdf location, and booleans on whether it has:
    - multiple tex files
    - an abstract (assumed false if nb of tex files > 1)
    - a bbl file
    - errors

Creates a .csv in the given base_dir. Assumes a structure of

base_dir
    /arxiv_extract
        /categories
            /extracted_source_folder
    /arxiv_raw
        /categories
            /source_pdfs
                /source
                    /raw_tarballs

The extracted_source_folder and the source_pdf should have the same names.


Implemented in Python 3.6

Published under the MIT License. 

Copyright 2017 by Jason Robert Webster.
"""

###############################################################################

from __future__ import print_function

import csv
import os
import random

###############################################################################

BASE_DIR = 'C:\\Data\\Text\\arxiv\\'
EXTRACT_FLD = 'arxiv_sources'
RAW_FLD = 'arxiv_raw'

###############################################################################

def random_tex(verbose=False):
    """
    Finds a random tex file. 
    Used to see what python intereprets a tex file as. 
    """

    base_dir = BASE_DIR
    extract_dir = os.path.join(base_dir, EXTRACT_FLD)

    # just open a tex file, any tex file
    # randomly choose a category
    categories = os.listdir(extract_dir)
    cat_choice = random.choice(categories)
    if verbose:
        print('Category ' + cat_choice + ' was randomly chosen.')

    # randomly choose a folder
    cat_dir = os.path.join(extract_dir, cat_choice)
    folders = os.listdir(cat_dir)
    folder_choice = random.choice(folders)
    if verbose:
        print('Folder ' + folder_choice + ' was randomly chosen.')

    # find tex files
    folder_dir = os.path.join(cat_dir, folder_choice)
    files = os.listdir(folder_dir)
    tex_files = []
    for f in files:
        f_dir = os.path.join(folder_dir, f)
        if f_dir.endswith('.tex'):
            tex_files.append(f_dir)
    
    # randomly open one
    tex_choice = random.choice(tex_files)
    if verbose:
        print('Final random dir: ' + tex_choice, end='\n\n')

    return tex_choice

###############################################################################

def print_tex(tex_file_dir):
    """
    Prints a tex file from a directory.
    """
    
    assert os.path.exists(tex_file_dir)
    assert tex_file_dir.endswith('.tex')

    with open(tex_file_dir) as fp:
        tex_contents = fp.read()

    print(tex_contents[:min(len(tex_contents)-1, 5000)])

###############################################################################

def return_tex(tex_file_dir):
    """
    Returns the contents of a tex file from a directory.
    """
    
    assert os.path.exists(tex_file_dir)
    assert tex_file_dir.endswith('.tex')

    with open(tex_file_dir) as fp:
        tex_contents = fp.read()

    return tex_contents

###############################################################################

def word_gen(tex_contents, filter=' .!}{)(,$%%][\\'):
    """
    Generator. Yields individual words from a string of contents. 
    """
    
    i = 0
    word = []
    while i <= len(tex_contents)-1:
        char = tex_contents[i]
        if char in filter:
            # only return words with an actual length
            if len(word) > 0:
                yield ''.join(word)
                word = []
            # yield the filtered char so that we can rebuild the string if needs be
            yield char
        else:
            word.append(char)
        i += 1

###############################################################################

def char_gen(tex_contents):
    """
    Generator. Yields individual chars from a string of contents. 
    """
    
    i = 0
    while i <= len(tex_contents)-1:
        yield tex_contents[i]
        i += 1

###############################################################################

def check_abstract(tex_contents):
    """
    Checks if the tex_contents have an abstract. 
    Only checks for \\begin{abstract} and \\abstract{
    Returns a tuple (abstract, start, end) where:
        abstract: whether or not the abstract exists
        start: where the abstact command starts
        end: where the abstract command ends
    """

    tex_seq = char_gen(tex_contents)
    char = ''
    # use two variables to track the commands I'm looking for
    # if the command matches a queue in the word_seqs, it will 
    # mean we've recognised a command and can start doing things
    commands = ['\\begin{abstract}', '\\abstract{']
    terminates = ['\\end{abstract}', '}']
    word_seqs = [[], []]
    term_seq = []
    command_found = -1
    nb_brackets = 0
    # init vars
    abstract = False
    index = 0
    start = -1
    end = -1

    while True:
        try:
            # get the next char from the tex sequence
            char = next(tex_seq)
            index += len(char)
        except StopIteration:
            return False, -1, -1
        
        # look for the command
        if abstract is False:
            # append this new word to the word seqs
            for word_seq in word_seqs:
                # build the queue by sliding a window over the text, the same
                # size as the length of one of our commands
                seq_index = word_seqs.index(word_seq)
                window_size = len(commands[seq_index])

                word_seq.append(char)
                if len(word_seq) > window_size:
                    word_seq.pop(0)
                
                if ''.join(word_seq) == commands[seq_index]:
                    abstract = True
                    start = index - window_size
                    command_found = seq_index
        
        # found the command, now get the return
        if abstract is True:
            if command_found == 0:
                # this is the \begin{abstract} clause
                # find a \end{abstract} clause end the statement
                term_seq.append(char)
                window_size = len(terminates[0])

                if len(term_seq) > window_size:
                    term_seq.pop(0)

                if ''.join(term_seq) == terminates[0]:
                    end = index # points to the } char
                    return abstract, start, end
            
            elif command_found == 1:
                # this is a \abstract{ clause
                # finding a '}' is too naive, we need to close the { case
                # on the first loop, the word should still be '{'
                if char == '{':
                    nb_brackets += 1
                if char == '}':
                    nb_brackets -= 1
                
                if nb_brackets <= 0:
                    # we closed the bracket
                    end = index #points to the } char
                    return abstract, start, end   

###############################################################################

def check_document(tex_contents):
    """
    Checks if the tex_contents have an \\begin{document} clause. 
    Returns a tuple (doc, start, end) where:
        doc: whether or not the document clause exists
        start: where the doc command starts
        end: where the doc command ends
    """
    # functionally identical to check_abstract with a few minor changes

    tex_seq = char_gen(tex_contents)
    char = ''
    # use two variables to track the commands I'm looking for
    # if the command matches a queue in the word_seqs, it will 
    # mean we've recognised a command and can start doing things
    commands = ['\\begin{document}']
    terminates = ['\\end{document}']
    word_seq = []
    term_seq = []
    # init vars
    doc = False
    index = 0
    start = -1
    end = -1

    while True:
        try:
            # get the next char from the tex sequence
            char = next(tex_seq)
            index += len(char)
        except StopIteration:
            return False, -1, -1
        
        # look for the command
        if doc is False:
            # append this new word to the word seqs
            # build the queue by sliding a window over the text, the same
            # size as the length of one of our commands
            word_seq.append(char)
            window_size = len(commands[0])

            if len(word_seq) > window_size:
                word_seq.pop(0)
            
            if ''.join(word_seq) == commands[0]:
                doc = True
                start = index - window_size
        
        # found the command, now get the return
        if doc is True:
            # this is the \begin{document} clause
            # find a \end{document} clause end the statement
            term_seq.append(char)
            window_size = len(terminates[0])

            if len(term_seq) > window_size:
                term_seq.pop(0)

            if ''.join(term_seq) == terminates[0]:
                end = index # points to the } char
                return doc, start, end

###############################################################################

def categorize(base_dir):
    """
    Main script that will create a .csv in the base dir with the following columns:
        source_dir: the directory of the source folder
        pdf_dir: the location of the associated pdf file
        cat: the category of the paper
        num_tex: int, the number of tex files
        abstract: boolean, returns if the article has an abstract (assumed false if above is >1)
        abs_start: int, the index where the abstract starts (at the command), -1 if abstract=False
        abs_end: int, the index where the abstract ends after the last }, -1 if abstract=False
        doc: boolean, returns if the article has a \\begin{document} command
        doc_start: int, starting point of command
        doc_end: int, end point of command
        num_bbl: int, returns the number of bbl files in the folder
        num_folder: boolean, returns true if the source_folder contain additional folders (such as a /figures folder) 
        error: whether an error occured at some stage in opening either the source .tex file or the .pdf file
    """

    # make sure the given dir exists and get the source extract dir
    assert os.path.exists(base_dir)
    extract_dir = os.path.join(base_dir, EXTRACT_FLD)
    csv_dir = os.path.join(base_dir, 'arxiv.csv')

    # get the categories
    cateories = os.listdir(extract_dir)

    csv_file = open(csv_dir, 'w', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow([
        'source_dir', 
        'pdf_dir', 
        'cat',
        'num_tex', 
        'abstract',
        'abs_start',
        'abs_end',
        'doc',
        'doc_start',
        'doc_end',
        'num_bbl',
        'num_folder',
        'error'
        ])

    rows = 0

    for cat in cateories:
        print(cat)
        cat_dir = os.path.join(extract_dir, cat)

        source_folders = os.listdir(cat_dir)
        for folder in source_folders:
            # initialize parameters
            num_tex = -1
            abstract = False
            abs_start = -1
            abs_end = -1
            doc = False
            doc_start = -1
            doc_end = -1
            num_bbl = -1
            num_folder = -1
            error = False
            # get the files in the folder
            folder_dir = os.path.join(cat_dir, folder)
            files = os.listdir(folder_dir)

            # count the number of files/folders
            tex_files = map(lambda x: x.endswith('.tex'), files)
            bbl_files = map(lambda x: x.endswith('.bbl'), files)
            folders = map(lambda x: os.path.isdir(os.path.join(folder_dir,x)), files)

            num_tex = sum(tex_files)
            num_bbl = sum(bbl_files)
            num_folder = sum(folders)

            if num_tex == 1:
                for f in files:
                    if f.endswith('.tex'):
                        f_dir = os.path.join(folder_dir, f)
                        try:
                            # reason for the try is multiple errors could come up
                            # and we don't know which errors to except
                            with open(f_dir, 'r') as fp:
                                tex_contents = fp.read()
                            abstract, abs_start, abs_end = check_abstract(tex_contents)
                            doc, doc_start, doc_end = check_document(tex_contents)
                        except:
                            error = True
                        finally:
                            break

            # this is the name of the pdf file
            name = folder + '.pdf'
            # get the equivalent directy in the raw folder and check it
            raw_dir = os.path.join(base_dir, RAW_FLD, cat, name)
            if os.path.exists(raw_dir):
                with open(raw_dir, 'rb') as fp:
                    if fp.readable() is False:
                        error = True

            # collect everything:
            # [source_dir, pdf_dir, num_tex, abstract, index, begin, num_bbl, num_folder, error]
            new_line = [folder_dir, raw_dir, cat, num_tex, abstract, abs_start, abs_end, doc, doc_start, doc_end, num_bbl, num_folder, error]
            csv_writer.writerow(new_line)
            rows += 1
    
    csv_file.close()
    print('Total entries: ' + str(rows))

###############################################################################

if __name__ == '__main__':
    categorize(BASE_DIR)
