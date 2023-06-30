# from .Whatsapp import *
import requests
import firebase_admin
import json

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
        dt = datetime.today()

        start = dt - timedelta(days=dt.weekday()+1)

        return start

    def get_last_day_week(self, dt):
        dt = datetime.today()

        start = dt - timedelta(days=dt.weekday()+1)
        end = start + timedelta(days=5)

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

        total_week_profit = 0.0
        total_week_balance = 0.0
        avg_accounts = 0
        
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
            drawdown = 0


            for account_id in doc_dict[u'accounts']:
                account = self.get_last_account_by_name(account_id, fmt_first_day)
                # print(account)

                if account != None and u'profit_loss' in account:
                    balance = account[u'balance']
                    profit_loss = account[u'profit_loss']
                    drawdown = account[u'drawdown']
                    equity = account[u'equity'] - balance

            percent = 0

            profit_loss = profit_loss + equity

            if profit_loss > 0:
                profit_loss = profit_loss 
                # - ( profit_loss * 0.08)
            elif profit_loss < 0:
                profit_loss = profit_loss 
                # + ( profit_loss * 0.08)

            if profit_loss != 0 and balance != 0:
                percent += ( profit_loss / balance ) * 100

            product_dict = {}
            product_dict[u'name'] = doc_dict[u'name']
            product_dict[u'profit_loss'] = profit_loss
            product_dict[u'drawdown'] = drawdown
            product_dict[u'balance'] = balance
            product_dict[u'equity'] = equity
            product_dict[u'percent'] = percent

            products_list.append(product_dict)

            avg_accounts += 1

            total_week_profit += profit_loss
            total_week_balance += balance

        avg_profit_percent = (total_week_profit / balance) * 100
        avg_profit = total_week_profit

        return_object['avg_profit_percent'] = avg_profit_percent
        return_object['week_profit'] = avg_profit

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
    
    def get_now_flat_date(self):
        dt = datetime.now().strftime("%d/%m/%Y")
        return dt
    
    def convert_to_date(self, date_string):
        dt = datetime.strptime(date_string, '%Y.%m.%d %H:%M:%S')
        return dt

    def get_clients(self):

        results = self.db.collection('clients').get()

        clients = []

        for doc in results:
            doc_dict = doc.to_dict()

            doc_accounts_array = doc_dict["accounts"]

            accounts = []

            for account in doc_accounts_array:
                account = self.get_account(account, to_date=self.get_now_flat_date())
                accounts.append(account)

            # clients["accounts"] = json.dumps(accounts)
            doc_dict["accounts"] = accounts
            clients.append(doc_dict)

        return clients

    def get_account(self, account_id, from_date = "01/01/1970", to_date = "01/01/1970"):

        results = self.db.collection('accounts').where('account_id', '==', account_id).order_by('start_scope', direction=firestore.Query.DESCENDING).limit(1).get()

        products = []

        from_date_time = datetime.strptime(from_date, '%d/%m/%Y')
        to_date_time = datetime.strptime(to_date, '%d/%m/%Y')

        for doc in results:
            doc_dict = doc.to_dict()
            total_profit_loss = 0.0

            if u'transactions' in doc_dict:
                transactions = doc_dict[u'transactions']

                for transaction in transactions:
                    profit = transaction['profit']
                    swap = transaction['swap']

                    transaction_close_date = datetime.strptime(
                        transaction["close_time"], '%Y.%m.%d %H:%M:%S')

                    if transaction_close_date >= from_date_time and transaction_close_date <= to_date_time and transaction["type"] != 0 and transaction["type"] != 1:
                        total_profit_loss += profit+(swap)

            decay = doc_dict[u'equity']-doc_dict[u'balance']
            decay_percent = decay / doc_dict[u'balance']

            doc_dict[u'decay'] = decay
            doc_dict[u'decay_percent'] = decay_percent

            doc_dict[u'profit_loss'] = total_profit_loss

            doc_dict.pop(u'transactions')
            doc_dict.pop(u'start_scope')
            doc_dict.pop(u'end_scope')
            doc_dict.pop(u'machine_name')
            
            products.append(doc_dict)

        return products
    
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