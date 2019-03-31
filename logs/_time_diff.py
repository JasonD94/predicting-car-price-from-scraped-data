from datetime import datetime

# Calculate how long the web scraper took to run
# http://strftime.org/
startTime = "03-31-19T16:30:19"
finishTime = "03-31-19T17:23:37"
dateTimeFmt = "%m-%d-%yT%H:%M:%S"

timeDiff = datetime.strptime(finishTime, dateTimeFmt) - datetime.strptime(startTime, dateTimeFmt)

print (f"Took {timeDiff} (hours : minutes : seconds) to run the web scraper with optimizations")

