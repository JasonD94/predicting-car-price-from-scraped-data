import bs4 as bs
from urllib.request import Request, urlopen
import pandas as pd
import logging

website = "https://www.thecarconnection.com"
csvFile = "new_cars.csv"

# Some logging for scraping.py, to both understand the script better and have debug info if it crashes
# or dies mid scrap. Logging is built into Python, info from: https://realpython.com/python-logging/
logging.basicConfig(filename='scrapping.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.info("This will get logged to  a file called scrapping.log")

def fetch(hostname, filename):
    return bs.BeautifulSoup(urlopen(Request(hostname + filename, headers={'User-Agent': 'X'})).read(), 'lxml')

# Grabs all the Makes on https://www.thecarconnection.com/new-cars
# Example: Ford, Chrysler, Toyota, etc
#  Format: https://www.thecarconnection.com//make/new,toyota
def all_makes():
    all_makes_list = []
    for a in fetch(website, "/new-cars").find_all("a", {"class": "add-zip"}):
        all_makes_list.append(a['href'])
        # Ex: Found Car Make: /make/new,toyota
        # <a class="add-zip " href="/make/new,toyota" title="Toyota">Toyota</a>
        logging.info("Found Car Make: %s", a['href'])
    return all_makes_list

# Grabs each model for a given make
# Example: Toyota Corolla
#  Format: https://www.thecarconnection.com/cars/toyota_corolla
def make_menu():
    make_menu_list = []
    for make in all_makes():
        for div in fetch(website, make).find_all("div", {"class": "name"}):
            make_menu_list.append(div.find_all("a")[0]['href'])
            # Ex: Found Model for /make/new,toyota: /cars/toyota_corolla
            # <a href="/cars/toyota_corolla">Toyota Corolla</a>
            logging.info("Found Model for %s: %s", make, div.find_all("a")[0]['href'])
    return make_menu_list

# Likely goes through the Make + Model?
def model_menu():
    model_menu_list = []
    for make in make_menu():
        soup = fetch(website, make)
        for div in soup.find_all("a", {"class": "btn avail-now first-item"}):
            model_menu_list.append(div['href'])
            # I think this gets the current model year, such as:
            # <a class="btn avail-now 1" href="/overview/toyota_corolla_2019" title="2019 Toyota Corolla Review">2019</a>
            # Which would be "2019"
            logging.info("Current Model Year: %s", div['href'])
        for div in soup.find_all("a", {"class": "btn 1"}):
            model_menu_list.append(div['href'])
            # Seems like this gets each additional Model Year, such as:
            # <a class="btn  1" href="/overview/toyota_corolla_2018" title="2018 Toyota Corolla Review">2018</a>
            # Which would be "2018"
            logging.info("Additional Model Years: %", div['href'])
    return model_menu_list

# Specs for each Make + Model + Year?
def year_model_overview():
    year_model_overview_list = []
    for make in model_menu():
        for id in fetch(website, make).find_all("a", {"id": "ymm-nav-specs-btn"}):
            year_model_overview().append(id['href'])
            print ("year_model_overview: " + id['href'])
    year_model_overview_list.remove("/specifications/buick_enclave_2019_fwd-4dr-preferred")
    return year_model_overview_list

def trims():
    trim_list = []
    print ("Trims Time")
    for row in year_model_overview():
        div = fetch(website, row).find_all("div", {"class": "block-inner"})[-1]
        div_a = div.find_all("a")
        print("Trims div: " + div)
        print("Trims div_a: " + div_a)
        for i in range(len(div_a)):
            trim_list.append(div_a[-i]['href'])
            print("i in range(len(div_a)): " + div_a[-i]['href'])
    return trim_list

print ("Starting scraping.py ...")
pd.DataFrame(trims()).to_csv(csvFile, index=False, header=None)
print ("Scrapping **DONE**")
trims = pd.read_csv(csvFile)

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

print ("Specifications time...")
specifications().to_csv(csvFile)
