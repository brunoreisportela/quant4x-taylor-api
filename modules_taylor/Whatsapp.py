import requests
import json

class Whatsapp:
    bearer = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIzOTRjYTg4Yy1iOTFlLTQ3ZDAtOTc3My04ZmFkNGEwYzBhNzkiLCJ1bmlxdWVfbmFtZSI6ImJydW5vQHF1YW50NHguY29tIiwibmFtZWlkIjoiYnJ1bm9AcXVhbnQ0eC5jb20iLCJlbWFpbCI6ImJydW5vQHF1YW50NHguY29tIiwiYXV0aF90aW1lIjoiMDcvMTcvMjAyMiAwNDowMTozNCIsImRiX25hbWUiOiIxMTIyMiIsImh0dHA6Ly9zY2hlbWFzLm1pY3Jvc29mdC5jb20vd3MvMjAwOC8wNi9pZGVudGl0eS9jbGFpbXMvcm9sZSI6IkFETUlOSVNUUkFUT1IiLCJleHAiOjI1MzQwMjMwMDgwMCwiaXNzIjoiQ2xhcmVfQUkiLCJhdWQiOiJDbGFyZV9BSSJ9.11ZDh3YneD_0Yzwq7k6PwPmpAclnjt3qTcft809o0-Q"

    def addContact(self, name, phone, payload):
        url = "https://live-server-11222.wati.io/api/v1/addContact/"+phone

        contact_payload = {
            "customParams": [
                {
                    "name": "system",
                    "value": "quant4x"
                }
            ],
            "name": name
        }

        headers = {
            "Content-Type": "text/json",
            "Authorization": self.bearer
        }

        response = requests.post(url, json=contact_payload, headers=headers)

        return self.sendIt(name, phone, payload)
        # return response.text

    def sendMessage(self, name, phone, payload):
        url = "https://live-server-11222.wati.io/api/v1/getContacts"

        phone = phone.strip()

        headers = {
            "Content-Type": "text/json",
            "Authorization": self.bearer
        }

        response = requests.get(url, headers=headers)

        contact_list_json = json.loads(response.text)

        is_contact_already_registered = False

        if "contact_list" in contact_list_json:
            for contact in contact_list_json["contact_list"]:
                print(contact)
                if contact["phone"].strip() == phone.strip():
                    is_contact_already_registered = True

        if is_contact_already_registered:
            return self.sendIt(phone, payload)
        else:
            return self.addContact(name, phone, payload)

    def sendIt(self, phone, payload):
        url = "https://live-server-11222.wati.io/api/v1/sendTemplateMessage?whatsappNumber="+phone

        # payload = {
        #     "broadcast_name": "new_user",
        #     "parameters": [
        #         {
        #             "name": "name",
        #             "value": "Bruno"
        #         }
        #     ],
        #     "template_name": "welcome_quant4x"
        # }
        
        headers = {
            "Content-Type": "text/json",
            "Authorization": self.bearer
        }     
        
        response = requests.post(url, json=payload, headers=headers)
        
        return response.text

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
