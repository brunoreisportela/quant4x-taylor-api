# from .Whatsapp import *
import requests
import firebase_admin

from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime, timedelta

class Firestore:

    cred = credentials.Certificate(u'quant4x-firebase-adminsdk-lf6g9-2b0a26729e.json')
    db = None

    def get_lorentzian(self, symbol_translate):
        lorentzian = self.db.collection(u'lorentzian').document(symbol_translate)

        doc = lorentzian.get()

        if doc.exists:
            return doc.to_dict()["direction"]
        else:
            return "neutral"

    def get_first_day_week(self, dt):
        # This is for getting from an specific date --- Test only ---
        # day = '06/04/2022'
        # dt = datetime.strptime(day, '%d/%m/%Y')

        # This is to get from the actual date -- Prod ---
        dt = datetime.today()

        start = dt - timedelta(days=dt.weekday()+1)
        end = start + timedelta(days=7)

        # print(start)
        # print(end)

        return start

    def get_last_day_week(self, dt):
        # This is for getting from an specific date --- Test only ---
        # day = '06/04/2022'
        # dt = datetime.strptime(day, '%d/%m/%Y')

        # This is to get from the actual date -- Prod ---
        dt = datetime.today()

        start = dt - timedelta(days=dt.weekday()+1)
        end = start + timedelta(days=5)

        # print(start)
        # print(end)

        return end
    
    def get_balance_from_list(self, balance_list, name):
        if name == "FX":
            name = "FOREX"
            
        for balance in balance_list:
            if balance[u'name'] == name:
                return balance[u'balance']
        
        return 0.0

    def get_products_performance(self):
        products_list = []
        return_object = {}
        # Update products active deposits

        balances = self.get_product_balance()
        
        # sync accounts data with the accounts in products
        products = self.db.collection(u'products')

        dt = datetime.today()
        first_day_week = self.get_first_day_week(dt)
        last_day_week = self.get_last_day_week(dt)

        fmt_first_day = first_day_week.strftime("%m/%d/%Y")

        for doc in products.get():
            doc_dict = doc.to_dict()

            balance = self.get_balance_from_list(balances, doc_dict[u'name'])
            profit_loss = 0
            equity = 0

            for account_id in doc_dict[u'accounts']:
                account = self.get_last_account_by_name(account_id, fmt_first_day)
                # print(account)

                if account != None and u'profit_loss' in account:
                    profit_loss += account[u'profit_loss']
                    equity += account[u'equity'] - account[u'balance']

            percent = 0

            profit_loss = profit_loss + equity

            if profit_loss > 0:
                profit_loss = profit_loss - ( profit_loss * 0.08)
            elif profit_loss < 0:
                profit_loss = profit_loss + ( profit_loss * 0.08)

            if profit_loss != 0 and balance != 0:
                percent += ( profit_loss / balance ) * 100

            product_dict = {}
            product_dict[u'name'] = doc_dict[u'name']
            product_dict[u'profit_loss'] = profit_loss
            product_dict[u'percent'] = percent

            products_list.append(product_dict)

        return_object['is_live'] = self.get_is_live(first_day_week, last_day_week)
        return_object['products'] = products_list

        return return_object

    def get_is_live(self, first_day_week, last_day_week):
        now_est = datetime.now()
        
        first_day_week_adjusted = first_day_week.replace(hour=20, minute=00)
        last_day_week_adjusted = last_day_week.replace(hour=22, minute=00)
        
        if now_est > first_day_week_adjusted and now_est < last_day_week_adjusted:
            return True
        else:
            return False
        
    def get_product_balance(self):
        headers = {'Accept': 'application/json'}

        balances = []

        try:
            r = requests.get('https://api.taylor.capital/status/investments', headers=headers)
            balances = r.json()[u'products']
        except KeyboardInterrupt:
            print(u'Error on getting balance data')

        return balances

    def get_last_account_by_name(self, account_id, fmt_first_day):
        accounts = self.db.collection(u'accounts')
        results = accounts.where(u'account_id', u'==', account_id).where(u'start_scope', '==', fmt_first_day).get()

        account_dict = None

        for doc in results:
            account_dict = doc.to_dict()

        return account_dict
    
    def get_accounts(self):

        accounts = self.db.collection(u'accounts')
        results = accounts.order_by(u'start_scope', direction=firestore.Query.DESCENDING).get()

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
                history_dict[u'balance'] = history_dict_from_account[u'balance']
                
                if u'equity' in history_dict_from_account:
                    history_dict[u'equity'] = history_dict_from_account[u'equity']

                history.append(history_dict)

            account_dict[u'profit_loss'] = history[len(history)-1][u'profit_loss']

            account_dict[u'history'] = history

            if self.findKeyInArray(products, doc_dict[u'account_id'], 'account_id') == False:
                products.append(account_dict)


        return products

    def findProductInArray(self, array, name):
        for item in array:
            if name == item:
                return True
        
        return False
    
    def findKeyInArray(self, array, name, key):
        for item in array:
            if item[key] == name:
                return True
        
        return False

    def __init__(self, *args, **kwargs):
        firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()

        super().__init__(*args, **kwargs)
