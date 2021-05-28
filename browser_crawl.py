#!/usr/local/bin/python3
##
## From the lolcrawler project
##
import os,string,random,sys,time,re
from selenium import webdriver  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from lxml import html
from sys import platform
from url_normalize import url_normalize
import requests
import tinycss2
from pprint import pprint
from bs4 import BeautifulSoup, SoupStrainer
from urllib.parse import urldefrag, urljoin, urlparse
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import Popularity
import timeout_decorator

@timeout_decorator.timeout(5) # 5 sec timeout on each url. 
def crawl1(base_url, url):

    if platform == "linux" or platform == "linux2":
        service = webdriver.chrome.service.Service("/usr/bin/chromedriver")
    elif platform == "darwin":
        service = webdriver.chrome.service.Service("/usr/local/bin/chromedriver")

    service.start()

    chrome_options = Options()  
    chrome_options.add_argument("--headless")  

    d = DesiredCapabilities.CHROME
    d['goog:loggingPrefs'] = { 'performance':'ALL' }

    opt = Options()

    opt.add_argument("start-maximized")
    opt.add_experimental_option("excludeSwitches", ["enable-automation"])
    opt.add_experimental_option('useAutomationExtension', False)

    opt.add_argument("--disable-infobars")
    opt.add_argument("--disable-extensions")
    opt.add_argument("--incognito") 
    opt.add_argument("--headless")
    opt.add_argument("--disable-background-networking")
    opt.add_argument("--disable-default-apps")
    opt.add_argument("--disable-extensions")
    opt.add_argument("--disable-gpu")
    opt.add_argument("--disable-sync")
    if platform == "linux" or platform == "linux2":
        opt.add_argument("--no-sandbox") # Needed when running in docker
    opt.add_argument("--disable-translate")
    opt.add_argument("--hide-scrollbars")
    opt.add_argument("--metrics-recording-only")
    opt.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36")
    opt.add_argument("--mute-audio")
    opt.add_argument("--no-first-run")
    opt.add_argument("--safebrowsing-disable-auto-update")
    # Pass the argument 1 to allow and 2 to block
    opt.add_experimental_option("prefs", { \
    "profile.default_content_setting_values.media_stream_mic": 1, 
    "profile.default_content_setting_values.media_stream_camera": 1,
    "profile.default_content_setting_values.geolocation": 1, 
    "profile.default_content_setting_values.notifications": 1 ,
    "webrtc.ip_handling_policy" : "disable_non_proxied_udp",
    "webrtc.multiple_routes_enabled": False,
    "webrtc.nonproxied_udp_enabled" : False
      })

    chrome_options.loggingPrefs = { 'browser':'ALL' }
    
    driver = webdriver.Remote(service.service_url,desired_capabilities=d, options=opt)
    driver.set_page_load_timeout(60)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    driver.get(url)
    ## Try with and without the following two lines
    #time.sleep(5)
    #driver.implicitly_wait(3)
    WebDriverWait(driver, 30).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    html_doc = driver.execute_script("return document.documentElement.outerHTML")
    #foo = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': events[0]["params"]["requestId"]})

    elems = driver.find_elements_by_tag_name('a')
    links1 = []
    for elem in elems:
        href = elem.get_attribute('href')
        if href is not None:
            links1.append(url_normalize(urljoin(url, href)))
    root = html.fromstring(html_doc)
    urls = root.xpath('//a/@href')
    links2 = []
    for e in urls:
        if e is not None:
            links2.append(url_normalize(urljoin(url, e)))

    return links1, links2, html_doc, driver.get_log('performance')

if __name__ == "__main__":
    main()
