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
        self.pre_prompt = "Please respond bullish, bearish, neutral"
        
    def get_feed(self):
        entries = []
        
        ticker = 'GBPUSD=X'

        rssfeedurl = 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=%s&region=US&lang=en-US'%ticker

        NewsFeed = feedparser.parse(rssfeedurl)
        NewsFeed.keys()
        
        range_max = len(NewsFeed.entries)

        if range_max > 3:
            range_max = 3

        for i in range(range_max):
            message = f'{NewsFeed.entries[i].title} {NewsFeed.entries[i].summary}'
            entries.append({"news": message, "result": self.get_response("GBPUSD", message)})

        ticker = 'EURUSD=X'

        rssfeedurl = 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=%s&region=US&lang=en-US'%ticker

        NewsFeed = feedparser.parse(rssfeedurl)
        NewsFeed.keys()
        
        range_max = len(NewsFeed.entries)

        if range_max > 3:
            range_max = 3

        for i in range(range_max):
            message = f'{NewsFeed.entries[i].title} {NewsFeed.entries[i].summary}'
            entries.append({"news": message, "result": self.get_response("EURUSD", message)})

        ticker = 'GC=F'

        rssfeedurl = 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=%s&region=US&lang=en-US'%ticker

        NewsFeed = feedparser.parse(rssfeedurl)
        NewsFeed.keys()
        
        range_max = len(NewsFeed.entries)

        if range_max > 3:
            range_max = 3

        for i in range(range_max):
            message = f'{NewsFeed.entries[i].title} {NewsFeed.entries[i].summary}'
            entries.append({"news": message, "result": self.get_response("GOLD", message)})

        return entries

    def get_response(self, ticker, input):

        input = input.replace("\"", "\n")

        # response = openai.Completion.create(
        #     model="text-davinci-003",
        #     prompt=f"{self.pre_prompt}\n {input}\n",
        #     max_tokens=800,
        #     temperature=0
        # )

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                    {"role": "user", "content": f"Given the ticker {ticker}, please respond only bullish, bearish or neutral to the following news: {input}\n"}
                ]
        )

        # response = openai.ChatCompletion.create(
        #     model="gpt-3.5-turbo",
        #     messages=[
        #         {"role": "user", "content": f"{self.pre_prompt}\n {input}\n"}
        #     ]
        # )

        if len(response.choices) > 0:
            return response.choices[0].message.content.replace("\n","")
        else:
            return "Error: No response could be obtained by Taylor this time."

    def __init__(self, *args, **kwargs):
        load_dotenv()

        openai.api_key = os.getenv("OPENAI_API_KEY")

        self.prepare()

        super().__init__(*args, **kwargs)
