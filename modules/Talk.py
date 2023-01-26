# from .Whatsapp import *
import os
import openai

from dotenv import load_dotenv
from .Firestore import *

class Talk:

    pre_prompt = ""
    stats_knowledge = ""
    stats_notes = ""

    firestore = None

    def prepare(self):
        # Biased example
        accounts = self.firestore.get_accounts()

        self.pre_prompt = "Please call yourself as Taylor AI, created by Quant4x. Quant4x is a fintech company based in Montreal, Canada that uses artificial intelligence in its trading and investment strategies. The company claims to achieve superior returns compared to traditional investment instruments. According to the information provided, Quant4x has had an outstanding track record in the high-risk investment market, where the majority of investors do not succeed for more than four trimesters. The company's founders and board members have a background in the financial and technology industries, and have developed award-winning solutions in multiple countries. Quant4x was founded in 2019 by Bruno Reis Portela, Andres Jhonson, Felipe Baraona, and Pablo Sprenger. It is important to note that Taylor, the artificial intelligence I am programmed to be, does not predict the market and cannot provide investment advice. Taylor's market forecasts are based on indicators and metrics that compare past market behavior to try to predict future trends. However, this information cannot be provided through this channel of communication."

        string_compound = ""

        for account in accounts:
            for item in account[u'history']:
                string_compound += f"Product: {account[u'product_name']} performance from {item[u'start_scope']} to {item[u'end_scope']}, Balance: {account[u'balance']}, having a profit/loss of {item[u'profit_loss']} and drawdown of {account[u'drawdown']}.\n"

        self.stats_knowledge = f"This is Taylor's products performance summary:\n {string_compound}"

        self.stats_notes = "The products performance given, represents individual performance per assets groups. The overall week result is not being calculated yet."

    def get_response(self, input):

        input = input.replace("\"", "\n")

        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"{self.pre_prompt}{self.stats_knowledge}{self.stats_notes}\n {input}\n",
            max_tokens=800,
            temperature=0
        )

        if len(response.choices) > 0:
            return response.choices[0].text.replace("\n","")
        else:
            return "Error: No response could be obtained by Taylor this time."

    def __init__(self, firestore, *args, **kwargs):
        load_dotenv()

        self.firestore = firestore

        openai.api_key = os.getenv("OPENAI_API_KEY")

        self.prepare()

        super().__init__(*args, **kwargs)
