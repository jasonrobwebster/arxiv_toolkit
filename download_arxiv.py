"""
Script for finding and downloading arXiv (arXiv.org) papers in bulk. 

Implemented in Python 3.6

Published under the MIT License. 

Copyright 2017 by Jason Robert Webster.
"""

###############################################################################

from __future__ import print_function

import os
import sys
import urllib.request
import urllib.error
import xmltodict
from time import sleep

###############################################################################

class DownloadError(OSError):
    """
    Custom error for failed downloads
    """
    pass

###############################################################################

def download(url, download_dir):
    """
    Downloads a url and places it into the download_dir. 
    """

    # the printhook for the download
    def printhook(chunks, block_size, total_size):
        """
        Prints the current download progress of a file.
        """
        
        if total_size > 0:
            # the total size is known
            percent_complete = min(float((chunks * block_size) / total_size * 100), 100)
            download_status = float((chunks * block_size)/1024/1024) #size in MB
            msg = "\rDownloading: %.1f%% (%.2fMB)" %(percent_complete, download_status)
        elif total_size == -1:
            # the total size is unknown
            download_status = float((chunks * block_size)/1024/1024) #size in MB
            msg = "\rDownloaded: %.2fMB" %download_status
        
        sys.stdout.write(msg)
        sys.stdout.flush()

    # Check to see if the dir is valid
    def is_dir_error():
        if not isinstance(download_dir, str):
            raise ValueError('The directory is not a string')
        if os.path.exists(download_dir) is False:
            raise ValueError('The directiory ' + dir + 'does not exist.')
        if os.path.isdir(download_dir) is False:
            raise ValueError('The directory ' + dir + 'is not a folder.')

    assert isinstance(url, str)
    # Gather data about the file
    filename = url.split('/')[-1]
    filename = filename
    file_path = os.path.join(download_dir, filename)

    if os.path.exists(file_path) is False:
        is_dir_error() # check for errors
        # Download the file
        urllib.request.urlretrieve(
            url=url,
            filename=file_path,
            reporthook=printhook
        )
        print(' ' + filename)
    else:
        raise DownloadError()

###############################################################################

def download_arxiv(num_papers_per_category, download_dir, category=None):
    """
    The main function. This will search for a collection of arxiv papers under 
    the scientific arxiv categories and save them to the appropriate location.
    """

    # Define the arxiv categories I want to download
    categories = [
        'astro-ph',
        'cond-mat',
        'gr-qc',
        'hep-ex',
        'hep-lat',
        'hep-ph',
        'hep-th',
        'math-ph',
        'nucl-ex',
        'nucl-th',
        'quant-ph',
        'cs.ai',
        'math.at'
    ]
    
    # if we've chosen a specific category or list thereof, let's just make our categories this list
    if category is not None:
        if isinstance(category, list):
            for cat in category:
                if cat in categories is False:
                    raise ValueError(cat + ' is not a valid category.')
            categories = category
        else:
            if category in categories:
                categories = [category]
            else:
                raise ValueError(category + ' is not a valid category.')
    
    count_papers = 0
    count_sources = 0

    # build the arxiv api url
    for cat in categories:
        # to ease the load on the server, we'll only request a maximum of num_results (1000) results at a time
        cat_dir = os.path.join(download_dir, cat)
        if os.path.exists(cat_dir):
            num_papers = len(os.listdir(cat_dir)) - 1
        else:
            num_papers = 0
        num_results = min(1000, num_papers_per_category)
        i = 0
        while num_papers < num_papers_per_category:
            # search via a particular category
            url = 'https://export.arxiv.org/api/query?search_query=cat:' + cat
            # get the right number of results
            start = i * num_results
            results = num_results + start
            url = url + '&start=' + str(start) + '&max_results=' + str(results)
            # sort the results by their date
            url = url + '&sortBy=lastUpdatedDate&sortOrder=descending'
            # update the loop
            i += 1

            # get the data from the server
            print('\nFetching data from ' + url)
            data_xml = urllib.request.urlopen(url).read()
            data_dict = xmltodict.parse(data_xml)
            print('Complete\n')

            # we now need the link to the paper
            for entry in data_dict['feed']['entry']:
                # check for the pdf key
                n = 0
                while n<=2:
                    if '@title' in entry['link'][n]:
                        if entry['link'][n]['@title'] == 'pdf':
                            break
                        else:
                            n += 1
                    else:
                        n += 1

                url_pdf = entry['link'][n]['@href']
                filename = url_pdf.split('/')[-1]

                # this is a pdf link, but sometimes lacks the '.pdf', add this
                if url_pdf.split('.')[-1] != 'pdf':
                    url_pdf = url_pdf + '.pdf'
                
                # to get the source file, change the url to get an e-print
                if filename.split('.')[-1] != 'pdf':
                    url_source_cat = 'https://arxiv.org/e-print/' + cat + '/' + filename
                    url_source = 'https://arxiv.org/e-print/' + filename
                else:
                    url_source_cat = 'https://arxiv.org/e-print/' + cat + '/' + os.path.splitext(filename)[0]
                    url_source = 'https://arxiv.org/e-print/' + os.path.splitext(filename)[0]

                # the download directory will be in C:/Data/Text/arXiv/cat/ and then source/ if we download a source
                pdf_dir = os.path.join(download_dir, cat)
                source_dir = os.path.join(pdf_dir, 'source')
                if os.path.exists(pdf_dir) is False:
                    os.makedirs(pdf_dir)
                if os.path.exists(source_dir) is False:
                    os.makedirs(source_dir)

                # try to download the paper
                try:
                    download(url_pdf, pdf_dir)
                    count_papers += 1
                    num_papers += 1
                except DownloadError:
                    print(filename + ' already exists in ' + pdf_dir)
                    count_papers += 1
                except urllib.error.ContentTooShortError:
                    # The download failed, but don't kill the program
                    print(filename + ' PDF failed to download. Check your connection.')
                    pdf_file_dir = os.path.join(pdf_dir, filename + '.pdf')
                    os.remove(pdf_file_dir)
                except urllib.error.URLError:
                    # The url does not exist
                    print (filename + ' PDF failed to download. The URL does not exist.')
                except ConnectionResetError:
                    print (filename + ' source failed to download. The connection was reset.')
                except TimeoutError:
                    print (filename + ' PDF failed to download. The URL timed out.')

                # try download the source
                try:
                    download(url_source, source_dir)
                    count_sources += 1
                except DownloadError:
                    print(filename + ' already exists in ' + source_dir)
                    count_sources += 1
                except urllib.error.ContentTooShortError:
                    # The download failed, but don't kill the program
                    print(filename + ' source failed to download. Check your connection.')
                    source_file_dir = os.path.join(source_dir, filename)
                    os.remove(source_file_dir)
                except urllib.error.URLError:
                    # The url does not exist
                    try:
                        download(url_source_cat, source_dir)
                        count_sources += 1
                    except:
                        print (filename + ' source failed to download. The URL does not exist.')
                except ConnectionResetError:
                    print (filename + ' source failed to download. The connection was reset.')
                except TimeoutError:
                    print (filename + ' source failed to download. The URL timed out.')

                # break if we have enough papers
                if num_papers >= num_papers_per_category:
                    break

                # ease load on the server by sleeping between paper downloads
                sleep(0.5)
            # sleep between major api requests
            sleep(2)
    
    # done downloading, print info
    print("Papers downloaded: %d \nSources downloaded: %d" %(count_papers, count_sources))

###############################################################################

def retrieve_sources(arxiv_dir, category=None):
    """
    Some papers did not download their source due to an incorrect url, this fixes that. 
    """

    # data dir to directory
    categories = os.listdir(arxiv_dir)

    if category is not None:
        if isinstance(category, list):
            for cat in category:
                if not cat in category:
                    raise ValueError(cat + ' is not a valid category.')
            categories = category
        else:
            if category in categories:
                categories = [category]

    count_sources = 0

    for cat in categories:
        print("\n" + cat)
        cat_dir = os.path.join(arxiv_dir, cat)
        files = os.listdir(cat_dir)

        for file in files:
            if file == 'source':
                break
            # get the filename sans the .pdf
            filename = os.path.splitext(file)[0]
            
            #get the download dir and urls
            download_dir = os.path.join(cat_dir,'source')
            url_source_cat = 'https://arxiv.org/e-print/' + cat + '/' + filename
            url_source = 'https://arxiv.org/e-print/' + filename

            # try downloading the source
            try:
                download(url_source, download_dir)
                count_sources += 1
            except urllib.error.ContentTooShortError:
                # The download failed, but don't kill the program
                print(filename + ' source failed to download. Check your connection.')
                os.remove(os.path.join(download_dir,filename))
            except urllib.error.HTTPError:
                print (filename + ' source failed to download. An HTTP error occured')
            except urllib.error.URLError:
                # The url does not exist
                try:
                    download(url_source_cat, download_dir)
                    count_sources += 1
                finally:
                    print (filename + ' source failed to download. The URL does not exist.')
            except TimeoutError:
                print (filename + ' source failed to download. The URL timed out.')
    
    print("\nSources downloaded: %d" %count_sources)

###############################################################################

if __name__ == '__main__':
    download_arxiv(500, 'C:/Data/Text/arxiv/arxiv_raw/')
