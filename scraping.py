import logging
import bs4 as bs
import pandas as pd
import aiohttp
import asyncio
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

website = "https://www.thecarconnection.com"
csvFile = "new_cars.csv"

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
year_model_overview_list = []
trim_list = []

# Async fetch for some super fast data minin'
async def asyncfetch(session, url):
    async with session.get(url) as response:
        if response.status != 200:
            response.raise_for_status()
            logging.critical("Failed to get async request!")
        logging.debug("Got response for: %s", url)
        return await response.text()

# Async gather - give it a session, and a list of URLs, fetches everything and returns it
async def async_fetch_all(session, urls):
    results = await asyncio.gather(*[asyncio.create_task(asyncfetch(session, url))
                                     for url in urls])
    return results

# Grabs all the Makes on https://www.thecarconnection.com/new-cars
# Example: Ford, Chrysler, Toyota, etc
#  Format: https://www.thecarconnection.com//make/new,toyota
# Appears to be 43 of these
def all_makes():

    # Now caching the makes list
    if (len(all_makes_list) == 0):

        for a in fetch(website, "/new-cars").find_all("a", {"class": "add-zip"}):
            all_makes_list.append(website + a['href'])
            # Ex: Found Car Make: /make/new,toyota
            # <a class="add-zip " href="/make/new,toyota" title="Toyota">Toyota</a>
            logging.debug("Found Car Make: %s", a['href'])

        # Log how many makes we found with a different level so we can easily find it later
        logging.info("Found %s Car Makes", len(all_makes_list))

    logging.info("Returning all_makes_list")
    return all_makes_list

# Grabs each model for a given make
# Example: Toyota Corolla
#  Format: https://www.thecarconnection.com/cars/toyota_corolla
# Appears to be *432* of these
async def all_make_models():

    # Trying some async Python for looping to make this go super quick (hopefully)
    # Results: 5 seconds quicker for this call.
    # https://stackoverflow.com/a/48052347
    # https://stackoverflow.com/a/35900453
    async with aiohttp.ClientSession() as session:
        results = await async_fetch_all(session, all_makes_list)

    for model in results:
        soup = BeautifulSoup(model, 'html.parser')

        for div in soup.find_all("div", {"class": "name"}):
            all_models_list.append(website + div.find_all("a")[0]['href'])
            # Ex: Found Model for /make/new,toyota: /cars/toyota_corolla
            # <a href="/cars/toyota_corolla">Toyota Corolla</a>
            logging.debug("Found Make Model Combo: %s", div.find_all("a")[0]['href'])

    # Log how many Make/Model combos we find
    logging.info("Found %s Make & Model Combinations", len(all_models_list))
    return all_models_list

# Grabs all the years for every given make/model combination
# Example: 2010 Toyota Corolla
#  Format: https://www.thecarconnection.com/overview/toyota_corolla_2010
# Appears to be *3931* of these
async def all_make_model_years():

    # Async call to get all make/model/year combos (3931 of these!)
    # Results: 
    async with aiohttp.ClientSession() as session:
        results = await async_fetch_all(session, all_models_list)

    for year in results:
        soup = BeautifulSoup(year, 'html.parser')

        for div in soup.find_all("a", {"class": "btn avail-now first-item"}):
            all_years_list.append(div['href'])
            # I think this gets the current model year, such as:
            # <a class="btn avail-now 1" href="/overview/toyota_corolla_2019" title="2019 Toyota Corolla Review">2019</a>
            # Which would be "2019"
            logging.debug("Current Model Year: %s", div['href'])
            
        for div in soup.find_all("a", {"class": "btn 1"}):
            all_years_list.append(div['href'])
            # Seems like this gets each additional Model Year, such as:
            # <a class="btn  1" href="/overview/toyota_corolla_2018" title="2018 Toyota Corolla Review">2018</a>
            # Which would be "2018"
            logging.debug("Additional Model Years: %s", div['href'])

    # Log how many Make/Model/Years combos we find
    logging.info("Found %s Make/Model/Year Combinations", len(all_years_list))
    return all_years_list

# Specs for each Make + Model + Year?
# TBD
def all_make_model_years_specs():

    # Cache all the data!1!!
    if(len(year_model_overview_list) == 0):
        for make in all_make_model_years():
            for id in fetch(website, make).find_all("a", {"id": "ymm-nav-specs-btn"}):
                # Pretty sure year_model_overview() needs to be year_model_overview_list,
                # otherwise we're going to have some infinite recursion with my optimizations
                year_model_overview_list.append(id['href'])
                logging.debug("year_model_overview: %s", id['href'])
        year_model_overview_list.remove("/specifications/buick_enclave_2019_fwd-4dr-preferred")

        # Log how many of these combos we find
        logging.info("Found %s Make/Model/Year/Spec Combinations", len(year_model_overview_list))

    logging.info("Returning year_model_overview_list")
    return year_model_overview_list

# This must be all the trims for a given Make/Model/Year, like:
# TBD
def trims():
    
    logging.info("Trims Time")

    if(len(trim_list) == 0):
        for row in all_make_model_years_specs():
            div = fetch(website, row).find_all("div", {"class": "block-inner"})[-1]
            div_a = div.find_all("a")
            logging.debug("Trims div: %s", div)
            logging.debug("Trims div_a: %s", div_a)
            for i in range(len(div_a)):
                trim_list.append(div_a[-i]['href'])
                logging.debug("i in range(len(div_a)): %s", div_a[-i]['href'])

        # Log how many of these combos we find
        logging.info("Found %s Make/Model/Year/Trim Combinations", len(trim_list))

    logging.info("Returning trim_list")
    return trim_list

logging.info("Starting scraping.py ...")

# Should be able to make some optimizations to gather all the data we need at once
# Like get all the makes, then fire off all the make_models
# When that completes, fire off all the make_model_years
# And when that's done, gather all the specs for make_model_year_specs
# Finally, ALL trims for every single make_model_year_specs
all_makes_list = all_makes()
all_models_list = asyncio.run(all_make_models())

logging.critical("Wow made it through all the make and models!")

all_years_list = asyncio.run(all_make_model_years())

logging.critical("Holy shit made it through all make model years!")

#model_menu_list = all_make_model_years()
#year_model_overview_list = all_make_model_years_specs()
#trim_list = trims()

pd.DataFrame(trims()).to_csv(csvFile, index=False, header=None)

logging.info("Scrapping **DONE**")
trims = pd.read_csv(csvFile)

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
specifications().to_csv(csvFile)
