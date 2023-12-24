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

pair = "EURUSD"

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

    content = dict()
    
    # Extract the JSON data
    pre = soup.find('body')

    content["url"] = url
    content["tile"] = soup.title.string
    # content["html"] = soup.find('body').prettify()

    pattern = re.compile('tv-widget-idea__description-row')

    # Find all elements with a class that matches the pattern
    content["ideas_and_timeline"] = []

    elements = soup.find_all(class_=pattern)

    # Process or print the elements
    for element in elements:
        content["ideas_and_timeline"].append(element.text.replace("\n","").replace("\t","").replace("\r","").strip())
    # You can process each element as per your requirement here

    json_ = json.dumps(content)

    return json_

def extract_between_braces(text):
    # This pattern finds all non-nested text between { and }
    pattern = r'\{([^}]*)\}'
    
    # re.findall returns all matches of the pattern in the string
    matches = re.findall(pattern, text)
    return matches

def fix_json(json_string):
    # Enclose keys in double quotes
    json_string = re.sub(r'(?<!")\b(\w+):\s', r'"\1": ', json_string)

    # Enclose string values in double quotes
    # This is a basic implementation and might not work for complex JSON strings.
    json_string = re.sub(r':\s*([a-zA-Z]\w*)(?=[,}])', r': "\1"', json_string)

    return json_string

if __name__ == "__main__":

    sentiment_pairs = dbController.get_sentiment_pairs()

    for sentiment_pair in sentiment_pairs:

        # sentiment_info = get_url_data(f"https://www.tradingview.com/symbols/{sentiment_pair["pair"]}/technicals/")
        # sentiment_info = get_url_data(f"https://www.tradingview.com/symbols/{sentiment_pair["pair"]}/")
        sentiment_info = get_url_data(f"https://www.tradingview.com/symbols/{sentiment_pair["pair"]}/ideas/")


        prompt = f"""Considering the current economic indicators or news available, what is the current sentiment for the pair {sentiment_pair["pair"]}?  Please answer with the following pattern {{ \"pair\":\"pair_symbol\",  \"sentiment\": \"bullish_or_bearish\" }}. This is the information available: {sentiment_info}"""

        get_result = dbController.taylor_get_answer(prompt)
        get_result = get_result.replace("\n","")
        get_result = fix_json(get_result)

        print(get_result)

        json_ = json.loads(get_result)

        dbController.save_sentiment_pair(sentiment_pair["pair"], json_["sentiment"])

        time.sleep(10)

    time.sleep(900)

        