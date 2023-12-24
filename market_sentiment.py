from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import re
import json
import time

from bs4 import BeautifulSoup

from modules import DBController

dbController = DBController()


def get_url_data(url):
    if url == None:
        return None
    # Set up the Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.headless = True  # Run in headless mode
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Open the URL
    driver.get(url)

    # Wait for the page to load (adjust the sleep time as necessary)
    time.sleep(3)

    # Extract the JSON data from the page
    json_ = convert_html_to_json(url, driver.page_source)
    
    return json_

def convert_html_to_json(url, html):
    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')

    url_info = dict()
    
    # Extract the JSON data
    pre = soup.find('body')

    url_info["url"] = url
    url_info["tile"] = soup.title.string
    url_info["html"] = soup.find('body').prettify()


    json_ = json.dumps(url_info)

    return json_


if __name__ == "__main__":
    get_url_data(f"https://www.tradingview.com/symbols/{pair}/technicals/")