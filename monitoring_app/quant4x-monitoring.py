import os
import argparse
import sys
import time

import json
import logging

# command to create one executable file
# PyInstaller --onefile --windowed quant4x-monitoring.py

from os import walk
from os import path
from datetime import datetime, timedelta

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("quant4x-firebase-adminsdk-lf6g9-2b0a26729e.json")

firebase_admin.initialize_app(cred)
db = firestore.client()

parser = argparse.ArgumentParser()

# for windows
parser.add_argument("-p", "--path", default="C:\\Users\\Extreme PC\\Documents\\node\\quant4x-dashboard\\python", help="Set MT4 main path")

args = parser.parse_args()

mt_path = args.path

def get_first_day_week(dt):
    dt = datetime.today()
    start = dt - timedelta(days=dt.weekday()+1)
    return start

def convert_to_date(date_string):
    dt = datetime.strptime(date_string, '%Y.%m.%d %H:%M:%S')
    return dt

def get_last_day_week(dt):
    dt = datetime.today()
    start = dt - timedelta(days=dt.weekday()+1)
    end = start + timedelta(days=7)
    return end    

def read_file(path):
    try:
        f = open(path, "r")

        data = json.load(f)

        dt = datetime.today()

        first_day_week = get_first_day_week(dt)
        last_day_week = get_last_day_week(dt)

        transactions = 0
        deposits = 0.0
        prior_profit = 0.0
        current_profit = 0.0

        for i in data['transactions']:
            transactions += 1
            transaction_close_date = datetime.strptime(
                i["close_time"], '%Y.%m.%d %H:%M:%S')

            if i["type"] != 0 and i["type"] != 1:
                deposits += i['profit']+(i['swap'])

            else:
                if transaction_close_date < first_day_week:
                    prior_profit += i['profit']+(i['swap'])

                if transaction_close_date >= first_day_week:
                    current_profit += i['profit']+(i['swap'])

        # print(transactions)
        # print(deposits)
        # print(prior_profit)
        # print(current_profit)
        # print(data["kpi"]["balance"])
    
        id = data['mt_account_id']
        fmt_first_day = first_day_week.strftime("%m_%d_%Y")
        fmt_last_day = last_day_week.strftime("%m_%d_%Y")

        date_scope = f"{data['mt_account_id']}-{fmt_first_day}-{fmt_last_day}"

        print( f"Account: {id} | date signature: {date_scope}" )
        
        doc_ref = db.collection(u'accounts').document(date_scope)
        doc_ref.set({
            u'account_id': f"{id}",
            u'drawdown': data["kpi"]["drawn_down"],
            u'balance': data["kpi"]["balance"],
            u'equity': data["kpi"]["equity"],
            u'start_scope': first_day_week.strftime("%m/%d/%Y"),
            u'end_scope': last_day_week.strftime("%m/%d/%Y"),
            u'machine_name': data["info"]["machine_name"],
            u'product_name': data["info"]["product_name"],
            u'profit_loss': current_profit,
            u'transactions': data['transactions']
        })

    except ValueError:
        print("Failure on opening a file")


def search_files():
    try:
        while True:
            for (dir_path, dir_names, file_names) in walk(mt_path):
                # for windows
                path_to_check = dir_path+"\\track_taylor.txt"

                if path.exists(path_to_check) == True:
                    read_file(path_to_check)

            time.sleep(60.0)

    except KeyboardInterrupt:
        print("Program finished by user.")
        pass


if __name__ == "__main__":
    # to test
    # read_file("track_taylor.txt")
    # pass

    try:
        search_files()
    except Exception as e:
        logging.critical(e, exc_info=True)  # log exception info at CRITICAL log level
        search_files()
        pass
