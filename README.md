## lolcrawler!

Headless browser crawler created for BugBounty and penetration-testing/RedTeaming. Beware, this code is really slow but should be able to run for several days and find some really interesting urls.

The crawler is using several different methods for trying to find links and urls such as BeautifulSoup, jsbeautifier, urlextract and linkfinder.py.

# Build docker image

Run the following command in the folder:

`docker rmi jonaslejon/lolcrawler ; docker build -t jonaslejon/lolcrawler .`

# Background

I wanted a tool similar to the Burp Suite crawler that I can run and forget about. Also parts of this code is powering the backend of WPSec.com
