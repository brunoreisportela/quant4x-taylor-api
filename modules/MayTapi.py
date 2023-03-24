import requests
import json
import sys

class MayTapi:
        
    INSTANCE_URL = "https://api.maytapi.com/api"
    PRODUCT_ID = "19e7fffc-1850-4b18-b276-f0d8f13b0b83"
    PHONE_ID = "17195"
    API_TOKEN = "1c619959-6dd6-4d7c-a532-295ee25fa692"

    def sendMessage(self, payload):
        payload = json.loads(payload)

        print("Request Body", payload, file=sys.stdout, flush=True)
        
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
