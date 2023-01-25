# from .Whatsapp import *
import os

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

class Firestore:

    cred = credentials.Certificate("quant4x-firebase-adminsdk-lf6g9-2b0a26729e.json")
    db = None
    
    def get_current_week_per_product_name(self):
        accounts = self.db.collection(u'accounts')

        query = accounts.order_by("start_scope")
        results = query.get()

        products = []

        for doc in results:
            
            print(f"{doc.id}")

            doc_dict = doc.to_dict()

            if self.findProductInArray(products, doc_dict["product_name"]) == False:
                products.append(doc_dict)

        return products
    
    def get_accounts(self):

        accounts = self.db.collection(u'accounts')
        results = accounts.get()

        products = []

        for doc in results:
            doc_dict = doc.to_dict()

            account_doc = self.db.collection(u'accounts').where(u'account_id', u'==', doc_dict[u'account_id'])

            account_dict = doc_dict

            account_dict.pop(u'end_scope')
            account_dict.pop(u'start_scope')
            
            history = []

            for account in account_doc.get():
                history_dict_from_account = account.to_dict()

                history_dict = {}
                history_dict[u'start_scope'] = history_dict_from_account[u'start_scope']
                history_dict[u'end_scope'] = history_dict_from_account[u'end_scope']
                history_dict[u'profit_loss'] = history_dict_from_account[u'profit_loss']

                history.append(history_dict)


            account_dict["profit_loss"] = history[len(history)-1]["profit_loss"]

            account_dict[u'history'] = history

            products.append(account_dict)


        return products

    def findProductInArray(self, array, name):
        for item in array:
            if name == item:
                return True
        
        return False

    def __init__(self, *args, **kwargs):
        firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()

        super().__init__(*args, **kwargs)
