import logging
import bs4 as bs
from urllib.request import Request, urlopen
import pandas as pd

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
all_makes_list = []
make_menu_list = []
model_menu_list = []
year_model_overview_list = []
trim_list = []

# Grabs all the Makes on https://www.thecarconnection.com/new-cars
# Example: Ford, Chrysler, Toyota, etc
#  Format: https://www.thecarconnection.com//make/new,toyota
# Appears to be 43 of these
def all_makes():

    # Now caching the makes list
    if (len(all_makes_list) == 0):
        for a in fetch(website, "/new-cars").find_all("a", {"class": "add-zip"}):
            all_makes_list.append(a['href'])
            # Ex: Found Car Make: /make/new,toyota
            # <a class="add-zip " href="/make/new,toyota" title="Toyota">Toyota</a>
            logging.debug("Found Car Make: %s", a['href'])

        # Log how many makes we found with a different level so we can easily find it later
        logging.info("Found %s Car Makes", len(all_makes_list))
    
    return all_makes_list

# Grabs each model for a given make
# Example: Toyota Corolla
#  Format: https://www.thecarconnection.com/cars/toyota_corolla
# Appears to be *432* of these
def make_menu():

    # Now caching Make_Models list
    if (len(make_menu_list) == 0):
        for make in all_makes():
            for div in fetch(website, make).find_all("div", {"class": "name"}):
                make_menu_list.append(div.find_all("a")[0]['href'])
                # Ex: Found Model for /make/new,toyota: /cars/toyota_corolla
                # <a href="/cars/toyota_corolla">Toyota Corolla</a>
                logging.debug("Found Model for %s: %s", make, div.find_all("a")[0]['href'])

        # Log how many Make/Model combos we find
        logging.info("Found %s Make & Model Combinations", len(make_menu_list))
    
    return make_menu_list

# Grabs all the years for every given make/model combination
# Example: 2010 Toyota Corolla
#  Format: https://www.thecarconnection.com/overview/toyota_corolla_2010
# TBD how many of these there are
def model_menu():

    # Caching the Make_Models_Years list
    if(len(model_menu_list) == 0):
        for make in make_menu():
            soup = fetch(website, make)
            for div in soup.find_all("a", {"class": "btn avail-now first-item"}):
                model_menu_list.append(div['href'])
                # I think this gets the current model year, such as:
                # <a class="btn avail-now 1" href="/overview/toyota_corolla_2019" title="2019 Toyota Corolla Review">2019</a>
                # Which would be "2019"
                logging.debug("Current Model Year: %s", div['href'])
            for div in soup.find_all("a", {"class": "btn 1"}):
                model_menu_list.append(div['href'])
                # Seems like this gets each additional Model Year, such as:
                # <a class="btn  1" href="/overview/toyota_corolla_2018" title="2018 Toyota Corolla Review">2018</a>
                # Which would be "2018"
                logging.debug("Additional Model Years: %s", div['href'])

        # Log how many Make/Model/Years combos we find
        logging.info("Found %s Make/Model/Year Combinations", len(model_menu_list))
    
    return model_menu_list

# Specs for each Make + Model + Year?
# TBD
def year_model_overview():

    # Cache all the data!1!!
    if(len(year_model_overview_list) == 0):
        for make in model_menu():
            for id in fetch(website, make).find_all("a", {"id": "ymm-nav-specs-btn"}):
                year_model_overview().append(id['href'])
                logging.debug("year_model_overview: %s", id['href'])
        year_model_overview_list.remove("/specifications/buick_enclave_2019_fwd-4dr-preferred")

        # Log how many of these combos we find
        logging.info("Found %s Make/Model/Year/Spec Combinations", len(year_model_overview_list))
    
    return year_model_overview_list

# This must be all the trims for a given Make/Model/Year, like:
# TBD
def trims():
    
    logging.info("Trims Time")

    if(len(trim_list) == 0):
        for row in year_model_overview():
            div = fetch(website, row).find_all("div", {"class": "block-inner"})[-1]
            div_a = div.find_all("a")
            logging.info("Trims div: %s", div)
            logging.info("Trims div_a: %s", div_a)
            for i in range(len(div_a)):
                trim_list.append(div_a[-i]['href'])
                logging.info("i in range(len(div_a)): %s", div_a[-i]['href'])

        # Log how many of these combos we find
        logging.info("Found %s Make/Model/Year/Trim Combinations", len(trim_list))
            
    return trim_list

logging.info("Starting scraping.py ...")
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
