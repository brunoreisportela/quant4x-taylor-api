# from .Whatsapp import *
import os
import openai
import json
import feedparser

from dotenv import load_dotenv

class NewsReader:

    pre_prompt = ""

    def prepare(self):
        # Biased example
        self.pre_prompt = "Please respond buy, strongly_buy, sell, strongly_sell or neutral to the given news:"
        
    def get_feed(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
        }

        ticker = 'GBPUSD=X'

        rssfeedurl = 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=%s&region=US&lang=en-US'%ticker

        NewsFeed = feedparser.parse(rssfeedurl)
        type(NewsFeed)
        NewsFeed.keys()
        len(NewsFeed.entries)
        NewsFeed.entries[0]

        entries = []

        for i in range(len(NewsFeed.entries)):
            message = f'{NewsFeed.entries[i].title} {NewsFeed.entries[i].summary}'
            entries.append({"news": message, "result": self.get_response(message)})

        return entries

    def get_response(self, input):

        # input = input.replace("\"", "\n")

        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"{self.pre_prompt}\n {input}\n",
            max_tokens=800,
            temperature=0
        )

        if len(response.choices) > 0:
            return response.choices[0].text.replace("\n","")
        else:
            return "Error: No response could be obtained by Taylor this time."

    def __init__(self, *args, **kwargs):
        load_dotenv()

        openai.api_key = os.getenv("OPENAI_API_KEY")

        self.prepare()

        super().__init__(*args, **kwargs)
