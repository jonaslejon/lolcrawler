#!/usr/local/bin/python3
# -*- coding: UTF-8 -*-
##
## Extract urls from webpage. Please run in Docker container due to selenium headless browser
## Jonas Lejon 2021-05-29 <jonas.lolcrawler@triop.se>
##
# pip3 install selenium webdriver-manager lxml jsbeautifier tinycss2 random_user_agent
# or pip3 install -r requirements.txt
#
# If running this directly on macOS, not recommended:
# brew install --cask chromedriver
# xattr -d com.apple.quarantine /usr/local/bin/chromedriver

VERSION="0.4"

import sys
if sys.version_info[0] < 3:
    raise SystemExit("Use Python 3 (or higher) only")

import os,string,random,time,re
import requests
import tinycss2
import traceback
import timeout_decorator
import argparse
from selenium import webdriver  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from lxml import html
from sys import platform
from url_normalize import url_normalize
from pprint import pprint
from bs4 import BeautifulSoup, SoupStrainer
from urllib.parse import urldefrag, urljoin, urlparse
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import Popularity
from urlextract import URLExtract
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Our own
from browser_crawl import crawl1

VERBOSE = False

# Credits to Gerben Javado, https://raw.githubusercontent.com/GerbenJavado/LinkFinder/master/linkfinder.py
from linkfinder import parser_file, regex_str

def main():
    global VERBOSE
    logo()
    parser = argparse.ArgumentParser()

    parser.add_argument('-o', '--output', help="Write links to this file", required=True)
    parser.add_argument('-u', '--url', help="Target website to crawl", dest="start_url", required=True)
    parser.add_argument('-v', '--verbose', help="increase output verbosity", action="store_true")
    parser.add_argument("-t", "--timeout", type=int, help="Adjust the timeout", default=5)
    args = parser.parse_args()

    VERBOSE = args.verbose

    crawl(args.start_url, args.output, args.timeout)

def crawl_debug(msg):
    if(VERBOSE):
        print(msg)
    return

def logo():
    print("\n    ╻  ┏━┓╻  ╻   ┏━╸┏━┓┏━┓╻ ╻╻  ┏━╸┏━┓")
    print("    ┃  ┃ ┃┃  ╹   ┃  ┣┳┛┣━┫┃╻┃┃  ┣╸ ┣┳┛")
    print("    ┗━╸┗━┛┗━╸╹   ┗━╸╹┗╸╹ ╹┗┻┛┗━╸┗━╸╹┗╸ lolcrawler version {0}\n".format(VERSION))
    print("    by Jonas Lejon\n")

# Extract urls using https://github.com/lipoja/URLExtract
def text2url(html):
    extractor = URLExtract()
    urls = extractor.find_urls(html)

    return urls

def save_output(status_code, url, output):
    with open(output, "a") as logfile:
        logfile.write("{}, {}\n".format(status_code, url))

# Main crawling function
def crawl(start_url, output, timeout):
    ## Figure out if we are redirected or now
    headers = {'User-Agent': random_agent()}

    print("Detecting redirects on start url: {0}".format(start_url))
    response = requests.get(start_url, headers=headers, verify=False)

    if response.history:
        print("- Redirecting to", fixup_url(response.url))
        base_url = fixup_url(response.url)
    else:
        base_url = fixup_url(start_url)

    base_netloc = urlparse(base_url).netloc

    seen = set()
    sitemap = set()
    todo = [base_url]
    external_links = []
    internal_links = []

    start = time.time()

    while todo:

        url = todo.pop()
        crawl_debug("Seen URLs: " + str(len(seen)) + ", todo URLs: " + str(len(todo)))
        status_code = 404 # Default status code

        try:
            status_code, external_links, internal_links = run_craw(base_url, url, base_netloc, timeout)
        except TypeError:
            pass
        except Exception as e:
            print("Error 3: Got exception",e,"on url",url)
            traceback.print_exc()
            pass

        ## Save to file
        save_output(status_code, url, output)
        sitemap.add((status_code, url))

        try:
            for abs_url in internal_links:
                if abs_url not in seen:
                    todo.append(abs_url)
                    seen.add(abs_url)
        except TypeError:
            pass 
        except Exception as e:
            print("Error 4: Got exception",e,"on url",url)
            traceback.print_exc()
            pass 

    end = time.time()

    print("Done crawling. Elapsed time: {} sec".format( round(end-start)))

def run_craw(base_url, url, base_netloc, timeout):

    url = fixup_url(url)

    # Remove some binary formats. Based on the content-type
    no_crawl = [ "application/font-woff", "image/png", "image/jpeg", "application/vnd.ms-fontobject", "application/octet-stream", "image/svg+xml" ]

    headers = {'User-Agent': random_agent()}

    print("Crawling {}".format(url))

    response = requests.get(url, headers=headers, verify=False)

    css_urls = []

    if response.headers['Content-Type'] == "text/css":
        css_urls = extract_urls_from_css(response.content.decode('utf-8'))

    if response.headers['Content-Type'] in no_crawl:
        crawl_debug("Not crawling " + url + " due to content-type: " + response.headers['Content-Type'])
        return response.status_code, None, None

    crawl_debug("Running Chromedriver headless on url: " + url)

    # Crawl using method 1 - Selenium webdriver headless
    try:
        links, links2, html, performance_data = crawl1(base_url, url)
    except timeout_decorator.timeout_decorator.TimeoutError:
        crawl_debug("Got timeout exception on url: " + url)
        return response.status_code, None, None
    except StaleElementReferenceException as Exception:
        crawl_debug("Got exception StaleElementReferenceException on url: " + url)
        return response.status_code, None, None

    crawl_debug("Extracting links from Python requests..")

    # Extract the links from method 1
    try:
        links3 = extract_links(response.content.decode('utf-8'), base_url)
    except UnicodeDecodeError:
        links3 = extract_links(response.content, base_url)

    links4 = extract_links(html, base_url)

    performance = ' '.join([str(elem).replace("u003C", "") for elem in performance_data]) # Remove \u003C garbage from Chrome performance data and flatten list (unicode U+003C < Less-than sign)
    performance = performance.replace("\\\\", "")
    performance = performance.replace("nhttps:", "https:")
    performance = performance.replace("nhttp:", "http:")

    # From LinkFinder
    endpoints = parser_file(performance, regex_str, mode=0, more_regex=None, no_dup=1)
    endpoints2 = parser_file(html, regex_str, mode=0, more_regex=None, no_dup=1)
    endpoints3 = parser_file(response.content.decode('utf-8'), regex_str, mode=0, more_regex=None, no_dup=1)

    all_endpoints = endpoints + endpoints2 + endpoints3
    linkfinder = []

    for key in all_endpoints:
        linkfinder.append(fixup_url( urljoin( base_url, key['link'])))

    text2url_links = text2url(html)
    text2url_links2 = text2url(response.content.decode('utf-8'))
    text2url_links3 = text2url(performance)

    all_text2url = text2url_links + text2url_links2 + text2url_links3

    urlextractor = []

    for a in all_text2url:
        if not re.match(r'^\*.', a) and not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",a): # Sometimes there is wildcard certificates. Do not include them
            urlextractor.append( fixup_url( a ) )

    auxiliaryList = list(set(links + links2 + links3 + links4 + urlextractor + linkfinder + css_urls))

    external_links = []
    internal_links = []

    for link in auxiliaryList:
        if urlparse(link).netloc != base_netloc:
            external_links.append(link)
        else:
            internal_links.append(link)

    return response.status_code, external_links, internal_links

def fixup_url(url):
    url, frag = urldefrag(url)
    url = url_normalize(url)
    return url

def random_agent():

    user_agent_rotator = UserAgent(popularity=Popularity.POPULAR.value, limit=100)

    user_agent = user_agent_rotator.get_random_user_agent()
    return user_agent

def extract_urls_from_html(html):
    dom = lxml.html.fromstring(html)
    return dom.xpath('//@href|//@src')

def extract_urls_from_css(css):
    urls = []
    rules = tinycss2.parse_stylesheet(css)
    for rule in rules:
        if rule.type == 'at-rule' and rule.lower_at_keyword == 'import':
            for token in rule.prelude:
                if token.type in ['string', 'url']:
                    urls.append(token.value)
        elif hasattr(rule, 'content'):
            for token in rule.content:
                if token.type == 'url':
                    urls.append(token.value)
    return urls

def extract_links(html, base_url):

    links = []

    for link in BeautifulSoup(html, 'html.parser', parse_only=SoupStrainer('a')):
        if link.has_attr('href'):
            links.append( fixup_url( urljoin( base_url, link.get('href') ) ))

    links2 = re.findall("href=[\"\'](.*?)[\"\']", html)
    links3 = re.findall("src=[\"\'](.*?)[\"\']", html)

    links2 = [ fixup_url( urljoin(base_url, i) ) for i in links2]
    links3 = [ fixup_url( urljoin(base_url, i) ) for i in links3]

    all_urls = links + links2 + links3

    auxiliaryList = list(set(all_urls))

    return auxiliaryList

if __name__ == "__main__":
    main()
