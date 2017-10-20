"""
Script for extracting arXiv source files after they've downloaded.
Assumes a level structure of:
base_dir
    /arxiv
        /categories
            /source
                /source_files

Implemented in Python 3.6

Published under the MIT License. 

Copyright 2017 by Jason Robert Webster.
"""

###############################################################################

from __future__ import print_function

import os
import tarfile

###############################################################################

def filter_dots(filename):
    """
    Some of the tarball names contain dots (e.g. 1710.04112). 
    This addresses that by filtering out the dots, returning 171004112. 
    """
    split = filename.split('.')
    out = ''
    for x in split:
        out = out + x

    return out

###############################################################################

def extract_tarfiles(base_dir, extract_dir):
    """
    Extracts files from base_dir to the extract_dir. 
    """

    # check validity of input
    if not os.path.exists(base_dir):
        raise ValueError('The base dir ' + dir + 'does not exist.')

    # create the dir to the arxiv
    arxiv_dir = os.path.join(base_dir, 'arxiv')
    categories = os.listdir(arxiv_dir)

    # loop over the categories
    for category in categories:
        print('\n' + category + '\n')
        source_dir = os.path.join(arxiv_dir, category, 'source')
        source_files = os.listdir(source_dir)

        #loop over the source files
        for source in source_files:
            # get the file
            file_dir = os.path.join(source_dir, source)
            if file_dir.endswith('.tar.gz'):
                filename = os.path.splitext(source)[0]
                filename = filter_dots(filename)
            else:
                filename = source
            
            # make the final_dir where the extracted files are placed
            final_dir = os.path.join(extract_dir, category, filename)

            if not os.path.exists(final_dir):
                # open the tarball
                print('Extracting ' + filename + '..', end=' ')
                try:
                    with tarfile.open(file_dir, 'r:gz') as tarball:
                        os.makedirs(final_dir)
                        tarball.extractall(final_dir)
                    print('Complete')
                except tarfile.ReadError:
                    print('Could not open tarball')
                except EOFError:
                    print('File caused an EOF error')
                
            else:
                print(final_dir + ' already exists.')

###############################################################################

if __name__ == '__main__':
    extract_tarfiles('C:/Data/Text/arxiv/', 'C:/Data/Text/arxiv_raw/arxiv_extract/')