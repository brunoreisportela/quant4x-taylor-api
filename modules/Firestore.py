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

    def findProductInArray(self, array, name):
        for item in array:
            if name == item:
                return True
        
        return False

    def __init__(self, *args, **kwargs):
        firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()

        super().__init__(*args, **kwargs)
