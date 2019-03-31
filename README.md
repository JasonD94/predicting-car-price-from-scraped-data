Scraping data from [The Car Connection](https://www.thecarconnection.com)
================================================================================

Original repo forked from [nicolas-gervais/predicting-car-price-from-scraped-data](https://github.com/nicolas-gervais/predicting-car-price-from-scraped-data)

Original Reddit post:
[I scraped 32,000 cars, including the price and 115 specifications](https://www.reddit.com/r/datasets/comments/b6rcwv/i_scraped_32000_cars_including_the_price_and_115/)

From the 
[/r/datasets](https://www.reddit.com/r/datasets/) subreddit

Modifying the [scraping.py](./scraping.py) Python Script to scrap the used 
car section, plus optimizing it using some async libraries like 
[aiohttp](https://aiohttp.readthedocs.io/en/stable/), 
[asyncio](https://docs.python.org/3/library/asyncio.html), and
[joblib](https://joblib.readthedocs.io/en/latest/index.html)
Also using [pickle](https://docs.python.org/3/library/pickle.html) 
to store the results of each scrap so we don't need to repeatedly
hit the same web pages multiple times.

Really interested in gathering some data on Toyota Sedans in my area:
[https://www.thecarconnection.com/inventory?make=toyota](https://www.thecarconnection.com/inventory?make=toyota)

# Running these scripts
To run, first install Python. You can find the latest and greatest Python version on [https://www.python.org/downloads/](https://www.python.org/downloads/)

Then, grab the [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/), 
[Requests](http://docs.python-requests.org/en/master/), 
and [pandas](https://pandas.pydata.org/)
python libraries. You can follow the Python User Guide
for [Installing Packages](https://packaging.python.org/tutorials/installing-packages/)

*Or*, run the following in bash/cmd:

1. Ensure pip, setuptools, and wheel are up to date:

```console
python -m pip install --upgrade pip setuptools wheel
```

2. Install Beautiful Soup, Request, urlopen, pandas

```console
pip install bs4 Request urlopen pandas
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; You should see messages like *"Successfully installed XYZ package"* in the console
window.

3. You might also need to install lxml if you run into an error running 
[scraping.py](./scraping.py). If you see the following error:

```
bs4.FeatureNotFound: Couldn't find a tree builder with the features you requested: lxml. 
Do you need to install a parser library?
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Then follow this [Stackoverflow post](https://stackoverflow.com/a/26856894), 
which basically says to install lxml:

```console
pip install lxml
```

4. My async version requires aiohttp, asyncio and to run parallel web requests
and process the specs data in parallel:

```console
pip install aiohttp joblib
```

[asyncio should be installed already, if not pip install it too]

5. Run the [scraping.py](./scraping.py) scipt using Python in bash/cmd or with
an IDE like [IDLE](https://docs.python.org/3/library/idle.html). The scraping
script takes a while to run, so give it a chance to run.

6. Run this script with **64 BIT PYTHON**. 32 Bit Python will throw memory exceptions
due to the insane number of URLs to scrap (~3800 - ~3900). The default download
on the python.org/downloads/ page is 32 bit - go directly to the latest version
of Python (3.7.3 as of this writing) and download the x86-64 version for your
platform. My machine is a 64 bit version of Windows 10, so I grabbed this download:

[Windows x86-64 executable installer](https://www.python.org/ftp/python/3.7.3/python-3.7.3-amd64.exe)

Which can be found here:
[python.org/downloads/release/python-373/](https://www.python.org/downloads/release/python-373/)

## *Random Note:* an IDLE Dark Mode Theme
Place [config-highlight.cfg](./config-highlight.cfg) inside **HOMEDIR**/.idlerc/ and go to 
Options → Configure IDLE → Highlights and switch on the "Custom Theme" 
(should default to Custom Dark), hit apply to turn it on.