# from .Whatsapp import *
import os
import openai

class Talk:

    pre_prompt = ""
    stats_knowledge = ""
    stats_notes = ""

    def prepare(self):
        # Biased example
        self.pre_prompt = ""
        self.pre_prompt = "Please call yourself as Taylor AI Assistant, created by Quant4x. Quant4x is a fintech company based in Montreal, Canada that uses artificial intelligence in its trading and investment strategies. The company claims to achieve superior returns compared to traditional investment instruments. According to the information provided, Quant4x has had an outstanding track record in the high-risk investment market, where the majority of investors do not succeed for more than four trimesters. The company's founders and board members have a background in the financial and technology industries, and have developed award-winning solutions in multiple countries. Quant4x was founded in 2019 by Bruno Reis Portela, Andres Jhonson, Felipe Baraona, and Pablo Sprenger. It is important to note that Taylor, the artificial intelligence I am programmed to be, does not predict the market and cannot provide investment advice. Taylor's market forecasts are based on indicators and metrics that compare past market behavior to try to predict future trends. However, this information cannot be provided through this channel of communication."
        # self.pre_prompt += "Taylor is The Future of Investing. A platform that democratizes access to real business investments and cutting-edge investment products. Our goal is to provide you with the necessary resources to conduct your own research and gain a better understanding of who we are and what we aim to accomplish. Please note that the content presented here is for informational purposes only and should not be considered as financial or investment advice. We encourage you to thoroughly research and perform due diligence before making any investments. It's important to remember that investment returns are never guaranteed and to invest wisely and safely. Taylor Capital leverages the benefits of DeFi to offer investment opportunities, previously exclusive to high-net-worth individuals via costly hedge funds, to a broader range of investors. Only pay a 10% fee on your profits. No deposits or hidden administration charges, every time you claim profits, the platform takes 10% of the claimed amount. Spread the word about your successful investment experience with Taylor Capital to your network. By sharing your referral link, you have the opportunity to earn a lifetime 1% commission on the profits claimed by those you refer."

    def get_response(self, input):

        input = input.replace("\"", "\n")

        # response = openai.Completion.create(
        #     model="text-davinci-003",
        #     prompt=f"{self.pre_prompt}{self.stats_knowledge}{self.stats_notes}\n {input}\n",
        #     max_tokens=800,
        #     temperature=0
        # )

        # if len(response.choices) > 0:
        #     return response.choices[0].text.replace("\n","")
        # else:
        #     return "Error: No response could be obtained by Taylor this time."


        completion = openai.ChatCompletion.create(
        model = 'gpt-3.5-turbo',
        messages = [ # Change the prompt parameter to the messages parameter
            {'role': 'system', 'content': f"{self.pre_prompt}\n {input}\n"},
        ],
            temperature = 0  
        )

        print(completion['choices'][0]['message']['content'])

        if len(completion['choices']) > 0:
            return completion['choices'][0]['message']['content']
        else:
            return "Error: No response could be obtained by Taylor this time."

    def __init__(self, *args, **kwargs):

        openai.api_key = os.getenv("OPENAI_API_KEY")

        self.prepare()

        super().__init__(*args, **kwargs)
