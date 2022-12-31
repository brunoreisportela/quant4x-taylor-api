# from .Whatsapp import *
import os
import openai


class Talk:

    def get_response(self, input):

        input = input.replace("\"", "\n")

        # Prompt example when data is available
        # prompt=f"Please call yourself as Taylor AI, created by Quant4x \n Some Taylor's products performance this week. Product: Metals with Balance of 529.47 dollars, drawndown of -50 dollars, week profit versus previous week is 29 dollars\n {input}\n",

        pre_prompt = "Please call yourself as Taylor AI, created by Quant4x. Quant4x is an A.I company, applied to the trading market. Obtaining systematically superior returns to traditional investment instruments. Within a market where 99% of all investors do not prevail more than four trimesters in a high-risk investment business, Quant4x, through technology boosted by A.I., had through time an outstanding result. Making us believe we are step by step, accomplishing our control risk through a high-risk market mission. All audited information. Quant4x is a fintech company based in Montreal, Canada, that develops artificial intelligence applied to investments. The founders and members of the board have more than 20 years of experience in the financial and technology industry developing award-winning solutions in multiple countries. Founded by Bruno Reis Portela, Andres Jhonson, Felipe Baraona and Pablo Sprenger in 2019."
        

        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=f"{pre_prompt}\n {input}\n",
            max_tokens=400,
            temperature=0
        )

        print(response.choices[0].text)

        return response

    def __init__(self, *args, **kwargs):
        openai.api_key = "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"

        super().__init__(*args, **kwargs)
