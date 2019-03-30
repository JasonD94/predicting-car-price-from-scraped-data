import logging
import bs4 as bs
import pandas as pd
import aiohttp
import asyncio
import pickle
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

website = "https://www.thecarconnection.com"
trimsCsvFile = "every_single_car.csv"
dataCsvFile = "the_big_data.csv"

print("************** Starting... **************")

# Some logging for scraping.py, to both understand the script better and have debug info if it crashes
# or dies mid scrap. Logging is built into Python
# https://realpython.com/python-logging/
logging.basicConfig(filename='scrapping.log',
                    filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%m-%d-%yT%H:%M:%S',
                    level=logging.DEBUG)

# Setup logging to the console too
# https://stackoverflow.com/a/38613204
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
# Format: DateTime: <message>
# http://strftime.org/
formatter = logging.Formatter('%(asctime)s: %(message)s', '%m-%d-%y %H:%M:%S')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logging.info('This will get logged to a file called scrapping.log')

def fetch(hostname, filename):
    return bs.BeautifulSoup(urlopen(Request(hostname + filename, headers={'User-Agent': 'X'})).read(), 'lxml')

# Code seems to be repeatedly calling out to the CarConnection website. No wonder it takes 8 hours to run currently...
# Instead, let's cache the basics like Makes & Models to speed this up.
all_makes_list = []     # Makes like Ford, Chevy
all_models_list = []    # Make_Models like Toyota Corolla
all_years_list = []     # Make_Model_Years like Toyota Corolla 2010
all_specs_list = []     # Make_Model_Year_Spec like Toyota Corolla 2010 XYZ
all_trims_list = []     # Make_Model_Year_Spec_Trim like Toyota Corolla 2010 XYZ ABC

# File Names for storing to & pulling from for future runs
all_makes_file = "txt_files/all_makes_file.txt"
all_models_file = "txt_files/all_models_file.txt"

# Async fetch for some super fast data minin'
async def asyncfetch(session, url, sem):
    try:
        async with sem:
            async with session.get(url) as response:
                if response.status != 200:
                    response.raise_for_status()
                    logging.critical("Failed to get async request!")
                logging.debug("Got response for: %s", url)
                return await response.text()
    except Exception as e:
        logging.error('exception: %s %s', type(e), str(e))
        return

# Async gather - give it a session, and a list of URLs, fetches everything and returns it
async def async_fetch_all(session, urls, sem):
    logging.info("async_fetch_all: %s %s %s", session, urls, sem)
    results = await asyncio.gather(*[asyncio.create_task(asyncfetch(session, url, sem))
                                     for url in urls])
    #logging.info("async_fetch_all returning: %s", results)
    return results

# Dump to file function
def dump2file(file_name, list_arr):
    with open(file_name, 'wb') as f:
        pickle.dump(list_arr, f)

def readFromfile(file_name):
    with open(file_name, 'rb') as f:
        list_arr = pickle.load(f)
        return list_arr

# Read from file function

# Grabs all the Makes on https://www.thecarconnection.com/new-cars
# Example: Ford, Chrysler, Toyota, etc
#  Format: https://www.thecarconnection.com//make/new,toyota
# Appears to be 43 of these
def all_makes():

    # Now caching the makes list
    try:
        all_makes_list = readFromfile(all_makes_file)
        if (len(all_makes_list) != 0):
            logging.info("Found all_makes_list, with %s Car Makes inside it", len(all_makes_list))
            logging.info("all_makes_list: %s", all_makes_list)
            return all_makes_list
        
    except Exception as e:
        logging.error("Didn't find the all_makes_list file, running scraper.py on it")
        all_makes_list = []
   
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

# Grabs each model for a given make
# Example: Toyota Corolla
#  Format: https://www.thecarconnection.com/cars/toyota_corolla
# Appears to be *432* of these
async def all_models():

    logging.critical("all_makes_list: %s", all_makes_list)

    # Don't overwhelm aiohttp!
    # 10 Requests *at most* at a time
    # https://pawelmhm.github.io/asyncio/python/aiohttp/2016/04/22/asyncio-aiohttp.html
    sem = asyncio.Semaphore(10)

    # Trying some async Python for looping to make this go super quick (hopefully)
    # Results: 5 seconds quicker for this call.
    # https://stackoverflow.com/a/48052347
    # https://stackoverflow.com/a/35900453
    async with aiohttp.ClientSession() as session:
        results = await async_fetch_all(session, all_makes_list, sem)

    for model in results:
        soup = BeautifulSoup(model, 'html.parser')

        for div in soup.find_all("div", {"class": "name"}):
            all_models_list.append(website + div.find_all("a")[0]['href'])
            # Ex: Found Model for /make/new,toyota: /cars/toyota_corolla
            # <a href="/cars/toyota_corolla">Toyota Corolla</a>
            logging.debug("Found Make Model Combo: %s", div.find_all("a")[0]['href'])

    # Log how many Make/Model combos we find
    logging.info("Found %s Make & Model Combinations", len(all_models_list))

# Grabs all the years for every given make/model combination
# Example: 2010 Toyota Corolla
#  Format: https://www.thecarconnection.com/overview/toyota_corolla_2010
# Appears to be *3931* of these
async def all_years():

    # Don't overwhelm aiohttp!
    # 10 Requests *at most* at a time
    # https://pawelmhm.github.io/asyncio/python/aiohttp/2016/04/22/asyncio-aiohttp.html
    sem = asyncio.Semaphore(10)

    # Async call to get all make/model/year combos (3931 of these!)
    # Results: 
    async with aiohttp.ClientSession() as session:
        results = await async_fetch_all(session, all_models_list, sem)

    for year in results:
        soup = BeautifulSoup(year, 'html.parser')

        for div in soup.find_all("a", {"class": "btn avail-now first-item"}):
            all_years_list.append(website + div['href'])
            # I think this gets the current model year, such as:
            # <a class="btn avail-now 1" href="/overview/toyota_corolla_2019" title="2019 Toyota Corolla Review">2019</a>
            # Which would be "2019"
            logging.debug("Current Model Year: %s", div['href'])
            
        for div in soup.find_all("a", {"class": "btn 1"}):
            all_years_list.append(website + div['href'])
            # Seems like this gets each additional Model Year, such as:
            # <a class="btn  1" href="/overview/toyota_corolla_2018" title="2018 Toyota Corolla Review">2018</a>
            # Which would be "2018"
            logging.debug("Additional Model Years: %s", div['href'])

    # Log how many Make/Model/Years combos we find
    logging.info("Found %s Make/Model/Year Combinations", len(all_years_list))

# Specs for each Make + Model + Year
# TBD
async def all_specs():

    # This call has ~3931 URLs, so we don't want to overwhelm aiohttp
    # Will limit it to 10 connections at the same time, and make it wait til those respond.
    # https://pawelmhm.github.io/asyncio/python/aiohttp/2016/04/22/asyncio-aiohttp.html
    sem = asyncio.Semaphore(10)

    # Async call to get all the specs for every make/model/year combo
    async with aiohttp.ClientSession() as session:
        # ALL_COMPLETED == don't return until every single make_model_year is found
        results = await asyncio.wait(async_fetch_all(session, all_years_list, sem), return_when=ALL_COMPLETED)

    for spec in results:
        soup = BeautifulSoup(spec, 'html.parser')

        for id in soup.find_all("a", {"id": "ymm-nav-specs-btn"}):
            # Pretty sure year_model_overview() needs to be year_model_overview_list,
            # otherwise we're going to have some infinite recursion with my optimizations
            all_specs_list.append(website + id['href'])
            logging.debug("year_model_overview: %s", id['href'])
    
    # Log how many of these combos we find
    logging.info("Found %s Make/Model/Year/Spec Combinations", len(all_specs_list))

# This must be all the trims for a given Make/Model/Year/Spec
# TBD
async def all_trims():
    
    # GATHER ALL THE TRIMS >:)
    async with aiohttp.ClientSession() as session:
        results = await async_fetch_all(session, all_specs_list)

    for trim in results:
        soup = BeautifulSoup(trim, 'html.parser')
        
        div = soup.find_all("div", {"class": "block-inner"})[-1]
        div_a = div.find_all("a")
        logging.debug("Trims div: %s", div)
        logging.debug("Trims div_a: %s", div_a)
        for i in range(len(div_a)):
            all_trims_list.append(div_a[-i]['href'])
            logging.debug("i in range(len(div_a)): %s", div_a[-i]['href'])

    # Log how many of these combos we find
    logging.info("Found %s Make/Model/Year/Trim Combinations", len(all_trims_list))

logging.info("Starting scraping.py ...")

# Optimized as much as I could out of this
# Order is:
# 1. Gather all Makes (Ford/Chevy/etc)
# 2. For each Make, gather all Models (Corolla, F150, etc)
# 3. For every Make/Model, gather all Years (2010, 2011, etc)
# 4. For every Make/Model/Year, gather all Specs
# 5. For every Make/Model/Year/Spec, gather all Trims
all_makes_list = all_makes()
logging.critical("Collected all Makes successfully")

# Now caching the models list
try:
    all_models_list = readFromfile(all_models_file)
    logging.info("Found this inside the all_models_file: %s", all_models_list)

    if (len(all_makes_list) != 0):
        logging.info("Found all_models_file, with %s Car Models inside it", len(all_models_list))
    else:
        logging.error("all_models_file is empty, running scraper.py on it")
        all_models_list = []
        asyncio.run(all_models())
    
except Exception as e:
    logging.error("Didn't find the all_models_file file, running scraper.py on it")
    all_models_list = []
    asyncio.run(all_models())

logging.critical("Collected all Models successfully")

# Write the makes to a file with the same name for easy retrieval.
logging.info("Car models list: %s", all_models_list)
dump2file(all_models_file, all_models_list)

#asyncio.run(all_years())
logging.critical("Collected all Years successfully")

#asyncio.run(all_specs())
logging.critical("Collected all Specs successfully")
#all_specs_list.remove("/specifications/buick_enclave_2019_fwd-4dr-preferred")

#asyncio.run(all_trims())
logging.critical("Collected all Trims successfully")

pd.DataFrame(all_trims_list).to_csv(trimsCsvFile, index=False, header=None)

logging.info("Scrapping **DONE**")
#trims = pd.read_csv(csvFile)

# This must grab specs for everything, looks like price + MSRP
def specifications():
    specifications_table = pd.DataFrame()
    
    for row in trims.iloc[:, 0]:
        soup = fetch(website, row)
        specifications_df = pd.DataFrame(columns=[soup.find_all("title")[0].text[:-15]])
        msrp_text = soup.find_all("div", {"class": "price"})[0]
        if len(msrp_text.find_all("a")) >= 1:
            specifications_df.loc["MSRP"] = msrp_text.find_all("a")[0].text
        for div in soup.find_all("div", {"class": "specs-set-item"}):
            row_name = div.find_all("span")[0].text
            row_value = div.find_all("span")[1].text
            specifications_df.loc[row_name] = row_value
        specifications_table = pd.concat([specifications_table, specifications_df], axis=1, sort=False)
    return specifications_table

logging.info("Specifications time...")
#specifications().to_csv(dataCsvFile)
