<img src="https://triop.se/wp-content/uploads/2021/05/lolcrawler.png" alt="LOLCrawler!">

# lolcrawler 🕷

Lolcrawler is a headless browser crawler created for BugBounty and penetration-testing/RedTeaming. Beware, this code is really slow but should be able to run for several days and find some really interesting urls/paths. 

The crawler is using several different methods for trying to find links and urls such as BeautifulSoup, jsbeautifier, urlextract and linkfinder.py.

You need to install docker to run this crawler due to the headless selenium browser. 

# Demo

Animated GIF:

<img src="https://triop.se/wp-content/uploads/2021/05/lolcrawler.gif" alt="lolcrawler demo" width="500" height="600">

## Run the crawler

### Option 1 

Download and run from Docker Hub:

```
docker pull jonaslejon/lolcrawler
mkdir output
docker run --rm -v `pwd`/output:/output -it jonaslejon/lolcrawler -u https://tor.triop.se -o /output/crawl.log
```

### Option 2

Download, build and run:

```
mkdir lolcrawler
cd lolcrawler
git clone https://github.com/jonaslejon/lolcrawler.git
docker build -t jonaslejon/lolcrawler .
docker run --rm -v `pwd`/output:/output -it jonaslejon/lolcrawler -u https://tor.triop.se -o /output/crawl.log
```

## Build docker image

Run the following command in the folder:

`docker rmi jonaslejon/lolcrawler ; docker build -t jonaslejon/lolcrawler .`


## About

I was looking for a tool similar to the Burp Suite crawler that I can run and forget about. Also parts of this code is powering the backend of [WPSec.com](https://wpsec.com).
