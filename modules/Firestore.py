# from .Whatsapp import *
import os

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

class Firestore:

    cred = credentials.ApplicationDefault()
    db = firestore.client()

    def __init__(self, *args, **kwargs):
        firebase_admin.initialize_app(self.cred)
        super().__init__(*args, **kwargs)
