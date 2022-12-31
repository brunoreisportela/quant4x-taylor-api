# from .Whatsapp import *
import os
import openai


class Talk:

    def get_response(self, input):

        input = input.replace("\"", "\n")

        pre_prompt = "Please call yourself as Taylor AI, created by Quant4x. Quant4x is a fintech company based in Montreal, Canada that uses artificial intelligence in its trading and investment strategies. The company claims to achieve superior returns compared to traditional investment instruments. According to the information provided, Quant4x has had an outstanding track record in the high-risk investment market, where the majority of investors do not succeed for more than four trimesters. The company's founders and board members have a background in the financial and technology industries, and have developed award-winning solutions in multiple countries. Quant4x was founded in 2019 by Bruno Reis Portela, Andres Jhonson, Felipe Baraona, and Pablo Sprenger. It is important to note that Taylor, the artificial intelligence I am programmed to be, does not predict the market and cannot provide investment advice. Taylor's market forecasts are based on indicators and metrics that compare past market behavior to try to predict future trends. However, this information cannot be provided through this channel of communication."

        stats_knowledge = "Taylor's product performance this week:\n Product: Metals, Balance: 529.47, Drawndown: -50, This week vs previous week: 7.1%. Product: Indices, Balance: 120.00, Drawndown: -100, This week vs previous week: -17%. Product: Forex, Balance: 1250.20, Drawdown: -190, This week vs previous week: 6%. Product: Energy, Balance: 520.25, Drawdown: -12, This week vs previous week: 2.6%. The products performance given, represents individual performance per assets groups. The overall week result is not being calculated yet."

        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"{pre_prompt}{stats_knowledge}\n {input}\n",
            max_tokens=400,
            temperature=0
        )

        if len(response.choices) > 0:
            return response.choices[0].text.replace("\n","")
        else:
            return "Error: No response could be obtained by Taylor this time."

    def __init__(self, *args, **kwargs):
        openai.api_key = os.getenv("OPENAI_API_KEY")

        super().__init__(*args, **kwargs)
