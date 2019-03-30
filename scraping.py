import logging
import bs4 as bs
import pandas as pd
import aiohttp
import asyncio
import pickle
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

website = "https://www.thecarconnection.com"

# File Names for storing to & pulling from for future runs
trimsCsvFile = "csv_files/every_single_car.csv"
dataCsvFile = "csv_files/the_big_data.csv"

all_makes_file = "txt_files/all_makes_file.txt"
all_models_file = "txt_files/all_models_file.txt"
all_years_file = "txt_files/all_years_file.txt"
all_specs_file = "txt_files/all_specs_file.txt"
all_trims_file = "txt_files/all_trims_file.txt"

# Code seems to be repeatedly calling out to the CarConnection website. No wonder it takes 8 hours to run currently...
# Instead, let's cache the basics like Makes & Models to speed this up.
all_makes_list = []     # Makes like Ford, Chevy
all_models_list = []    # Make_Models like Toyota Corolla
all_years_list = []     # Make_Model_Years like Toyota Corolla 2010
all_specs_list = []     # Make_Model_Year_Spec like Toyota Corolla 2010 XYZ
all_trims_list = []     # Make_Model_Year_Spec_Trim like Toyota Corolla 2010 XYZ ABC

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

# Format = DateTime: <message>
# http://strftime.org/
formatter = logging.Formatter('%(asctime)s: %(message)s', '%m-%d-%y %H:%M:%S')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# Logging should be working now
logging.info("************** Starting... **************")
logging.info('This will get logged to a file called scrapping.log')

# Original fetch function
def fetch(hostname, filename):
    return bs.BeautifulSoup(urlopen(Request(hostname + filename, headers={'User-Agent': 'X'})).read(), 'lxml')

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
        logging.error('aiohttp exception: %s %s', type(e), str(e))
        return

# Async gather - give it a session, and a list of URLs, fetches everything and returns it
async def async_fetch_all(session, urls, sem):
    logging.info("async_fetch_all: %s %s", len(urls), sem)
    results = await asyncio.gather(*[asyncio.create_task(asyncfetch(session, url, sem))
                                     for url in urls], return_exceptions=True)
    return results

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

    # Write the models to a file with the same name for easy retrieval.
    dump2file(all_models_file, all_models_list)

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

    # Write the years to a file with the same name for easy retrieval.
    dump2file(all_years_file, all_years_list)

# Specs for each Make + Model + Year
# Appears to be around 3812 of these
async def all_specs():

    # This call has ~3931 URLs, so we don't want to overwhelm aiohttp
    # Will limit it to 5 connections at the same time, and make it wait til those respond.
    # https://pawelmhm.github.io/asyncio/python/aiohttp/2016/04/22/asyncio-aiohttp.html
    sem = asyncio.Semaphore(5)

    # Async call to get all the specs for every make/model/year combo
    async with aiohttp.ClientSession() as session:
        # This works, but may cause results to be empty. Need to investigate it more.
        results = await async_fetch_all(session, all_years_list, sem)

        # TODO: Look more into this article
        # https://hackernoon.com/threaded-asynchronous-magic-and-how-to-wield-it-bba9ed602c32
        
        # This is tricky, if needed come back and try to get this working
        # https://docs.python.org/3/library/asyncio-task.html#running-tasks-concurrently
        # https://stackoverflow.com/questions/34509586/how-to-know-which-coroutines-were-done-with-asyncio-wait
        # https://stackoverflow.com/questions/52245922/is-it-more-efficient-to-use-create-task-or-gather
        # ALL_COMPLETED == don't return until every single make_model_year is found
        #http_task = asyncio.ensure_future(async_fetch_all(session, all_years_list, sem))

    # Seems like 3931 URLs can cause the await to not really wait... so check for empty lists first
    if results:
        for spec in results:
            soup = BeautifulSoup(spec, 'html.parser')

            for id in soup.find_all("a", {"id": "ymm-nav-specs-btn"}):
                # Pretty sure year_model_overview() needs to be year_model_overview_list,
                # otherwise we're going to have some infinite recursion with my optimizations
                all_specs_list.append(website + id['href'])
                logging.debug("year_model_overview: %s", id['href'])
    
    # Log how many of these combos we find
    logging.info("Found %s Make/Model/Year/Spec Combinations", len(all_specs_list))

    # Write the specs to a file
    dump2file(all_specs_file, all_specs_list)

# This must be all the trims for a given Make/Model/Year/Spec
# Turns out there's ~32321 Make/Model/Year/Trim Combinations! Jeez.
async def all_trims():

    # Same as all_specs(), this has ~3800 URLs to hit so limit of 4 concurrent requests
    # to avoid overwhelming the server
    sem = asyncio.Semaphore(5)
    
    # GATHER ALL THE TRIMS!1!1
    async with aiohttp.ClientSession() as session:
        results = await async_fetch_all(session, all_specs_list, sem)

    # Seems like 3812 URLs can cause the await to not really wait... so check for empty lists first
    if results:
        for trim in results:
            if trim:
                soup = BeautifulSoup(trim, 'html.parser')
                
                div = soup.find_all("div", {"class": "block-inner"})[-1]
                div_a = div.find_all("a")
                logging.debug("Trims div: %s", div)
                logging.debug("Trims div_a: %s", div_a)

                #
                # Ran into an exception on the len(div_a) call. I think the original code this is based on
                # must have ran into the same problem, based on the following snippet of code I spotted:
                # year_model_overview_list.remove("/specifications/buick_enclave_2019_fwd-4dr-preferred")
                # The exception I saw happened around here at this make_model_year_spec:
                # /specifications/buick_encore_2013_awd-4dr-convenience
                #
                # Since it's possible for this to happen anywhere if the pages aren't 100% the same setup,
                # we should wrap this in a try/except and log any weird errors we run into.
                try:
                    for i in range(len(div_a)):
                        all_trims_list.append(website + div_a[-i]['href'])
                        logging.debug("i in range(len(div_a)): %s", div_a[-i]['href'])

                except Exception as e:
                    logging.error('all_trims exception at for i in range(len(div_a)): %s %s', type(e), str(e))
                    return
            else:
                # Actually, seems like one of the trims might just be coming back as null for some reason...
                logging.error("found a null trim: %s", trim)

    # Log how many of these trim combos we find
    logging.info("Found %s Make/Model/Year/Trim Combinations", len(all_trims_list))

    # Write the trims to a file
    dump2file(all_trims_file, all_trims_list)

logging.info("Starting scraping.py ...")

# Optimized as much as I could out of this. Async http & cache results to files.
# Order is:
# 1. Gather all Makes (Ford/Chevy/etc)
# 2. For each Make, gather all Models (Corolla, F150, etc)
# 3. For every Make/Model, gather all Years (2010, 2011, etc)
# 4. For every Make/Model/Year, gather all Specs
# 5. For every Make/Model/Year/Spec, gather all Trims
all_makes_list = all_makes()
logging.critical("Collected all Makes successfully")

# Now caching the models list
all_models_list = try2readfile("all_models_list", all_models_list, all_models_file, all_models)
logging.info("Size of all_models_list: %s", len(all_models_list))

# Now caching the years list
all_years_list = try2readfile("all_years_list", all_years_list, all_years_file, all_years)

# Now caching the specs list
all_specs_list = try2readfile("all_specs_list", all_specs_list, all_specs_file, all_specs)

# Now caching the trims list
all_trims_list = try2readfile("all_trims_list", all_trims_list, all_trims_file, all_trims)

# Write this all out to a CSV file in csv_files
pd.DataFrame(all_trims_list).to_csv(trimsCsvFile, index=False, header=None)

logging.info("Scrapping Make/Model/Year/Spec/Trim **DONE**")

# This must grab specs for everything, looks like price + MSRP
async def specifications():
    # 32,000 URLs to hit, so limit of 5 concurrent requests to avoid overwhelming the server
    sem = asyncio.Semaphore(5)
    
    # GATHER ALL THE SPECS!1!1
    async with aiohttp.ClientSession() as session:
        results = await async_fetch_all(session, all_trims_list, sem)
             
    specifications_table = pd.DataFrame()

    if results:
        for row in results:
            soup = BeautifulSoup(row, 'html.parser')
             
            specifications_df = pd.DataFrame(columns=[soup.find_all("title")[0].text[:-15]])

            # Let's see what this pulls back
            logging.debug("specifications_df: %s", specifications_df)
            
            msrp_text = soup.find_all("div", {"class": "price"})[0]
            logging.debug("msrp_text: %s", msrp_text)
            
            if len(msrp_text.find_all("a")) >= 1:
                specifications_df.loc["MSRP"] = msrp_text.find_all("a")[0].text
                logging.debug("msrp_text: %s", specifications_df.loc["MSRP"])
                
            for div in soup.find_all("div", {"class": "specs-set-item"}):
                row_name = div.find_all("span")[0].text
                row_value = div.find_all("span")[1].text
                specifications_df.loc[row_name] = row_value
                logging.debug("Row name: %s", row_name)
                logging.debug("Row value: %s", row_value)
                
            specifications_table = pd.concat([specifications_table, specifications_df], axis=1, sort=False)

    #        #DONE
    logging.info("Finishing scrapin' specs")
    return specifications_table

# With all 32,000 vehicles, we can finally pull in all their specs. Woo hoo!
logging.info("Specifications Scrapin' time!1!")
specs_csv = asyncio.run(specifications())

if specs_csv:
   specs_csv.to_csv(dataCsvFile)

logging.info("Finished getting data!")



