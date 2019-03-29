Scraping data from [The Car Connection](https://www.thecarconnection.com)
================================================================================

Original repo forked from [nicolas-gervais/predicting-car-price-from-scraped-data](https://github.com/nicolas-gervais/predicting-car-price-from-scraped-data)

Modifying to scrap the used car section

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

4. Run the [scraping.py](./scraping.py) scipt using Python in bash/cmd or with
an IDE like [IDLE](https://docs.python.org/3/library/idle.html). The scraping
script takes a while to run, so give it a chance to run.

## *Random Note:* an IDLE Dark Mode Theme
Place [config-highlight.cfg](./config-highlight.cfg) inside **~HOMEDIR~**/.idlerc/ and go to 
Options → Configure IDLE → Highlights and switch on the "Custom Theme" 
(should default to Custom Dark), hit apply to turn it on.