import requests
import json
import sys

from modules import Talk

class MayTapi:

    talk = Talk()

    INSTANCE_URL = "https://api.maytapi.com/api"
    PRODUCT_ID = "19e7fffc-1850-4b18-b276-f0d8f13b0b83"
    PHONE_ID = "17195"
    API_TOKEN = "1c619959-6dd6-4d7c-a532-295ee25fa692"

    def setup_webhook(self):

        url = self.INSTANCE_URL + "/" + self.PRODUCT_ID + "/setWebhook"

        print("url", url, file=sys.stdout, flush=True)
        
        headers = {
            "Content-Type": "application/json",
            "x-maytapi-key": self.API_TOKEN,
        }
        
        body = {"webhook": "https://taylor-api.quant4x.com/webhook"}
        
        response = requests.post(url, json=body, headers=headers)
        
        print("webhook ", response.json())

    def send_message(self, payload):

        if isinstance(payload, str):
            payload = json.loads(payload)

        # talk_response = self.talk.get_response(f"""Send the following message, rephrasing it, keep it simple and objective, however, still personal enough to make it look like a real person behind the answers: {payload["message"]}""")

        talk_response = payload["message"]

        payload.update({"message": talk_response})

        url = self.INSTANCE_URL + "/" + self.PRODUCT_ID + "/" + self.PHONE_ID + "/sendMessage"

        headers = {
            "Content-Type": "application/json",
            "x-maytapi-key": self.API_TOKEN,
        }

        response = requests.post(url, json=payload, headers=headers)
        
        print("Response", response.json(), file=sys.stdout, flush=True)

        return response.json()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.setup_webhook()
