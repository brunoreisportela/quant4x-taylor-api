# from .Whatsapp import *
import os

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

class Firestore:

    cred = credentials.Certificate("quant4x-firebase-adminsdk-lf6g9-2b0a26729e.json")
    db = None

    def __init__(self, *args, **kwargs):
        firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()

        super().__init__(*args, **kwargs)
