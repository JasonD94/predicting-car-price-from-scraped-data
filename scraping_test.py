import logging
import bs4 as bs
import pandas as pd
import pickle
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

website = "https://www.thecarconnection.com"
all_makes_file = "txt_files/all_makes_file.txt"
all_makes_list = []     # Makes like Ford, Chevy

# File IO functions - caching results of previous web scraps, so if we crash or timeout, or whatever
# we won't have to grab the same data repeatedly. In the future, we can overwrite these files or
# add an option to delete them if we want fresh data (perhaps a new model came out recently)
# Also turning this into a function vs copy/pasting the same copy 4 times. :]
def try2readfile(scrap_name, scrap_list, scrap_file, async_function):
    # Now caching the models list
    try:
        scrap_list = readFromfile(scrap_file)

        if (len(scrap_list) != 0):
            logging.info("Found %s, with %s entries", scrap_name, len(scrap_list))
        else:
            logging.error("%s is empty, running web scraper", scrap_file)
            scrap_list = []
            asyncio.run(async_function())
        
    except Exception as e:
        logging.error("Didn't find the %s file, running scraper", scrap_file)
        scrap_list = []
        asyncio.run(async_function())

    logging.critical("Collected all %s successfully", scrap_name)
    return scrap_list

def readFromfile(file_name):
    with open(file_name, 'rb') as f:
        list_arr = pickle.load(f)
        return list_arr

def dump2file(file_name, list_arr):
    with open(file_name, 'wb') as f:
        pickle.dump(list_arr, f)

def fetch(hostname, filename):
    return bs.BeautifulSoup(urlopen(Request(hostname + filename, headers={'User-Agent': 'X'})).read(), 'lxml')

# Grabs all the Makes on https://www.thecarconnection.com/new-cars
# Example: Ford, Chrysler, Toyota, etc
#  Format: https://www.thecarconnection.com//make/new,toyota
# Appears to be 43 of these
def all_makes():

    # If we didn't find the cache list, bombs away
    for a in fetch(website, "/new-cars").find_all("a", {"class": "add-zip"}):
        all_makes_list.append(website + a['href'])
        # Ex: Found Car Make: /make/new,toyota
        # <a class="add-zip " href="/make/new,toyota" title="Toyota">Toyota</a>
        logging.debug("Found Car Make: %s", a['href'])

    # Log how many makes we found with a different level so we can easily find it later
    logging.info("Found %s Car Makes", len(all_makes_list))

    # Write the makes to a file with the same name for easy retrieval.
    logging.info("Car makes list: %s", all_makes_list)
    dump2file(all_makes_file, all_makes_list)

    return all_makes_list
    
# Make a test version of the files (just 4 makes to test with)
all_makes_list = all_makes()
logging.critical("Collected all Makes successfully")
test_makes_list = all_makes_list[0:3]
dump2file("txt_files/test/test_makes_file.txt", test_makes_list)


