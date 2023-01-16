import os
import argparse
import sys
import time

import json

from os import walk
from os import path
from datetime import datetime, timedelta

parser = argparse.ArgumentParser()

# for windows
# parser.add_argument("-p", "--path", default="C:\\Users\\Extreme PC\\Documents\\node\\quant4x-dashboard\\python", help="Set MT4 main path")

# for mac
parser.add_argument("-p", "--path", default="/Users/babablacksheep/projects/python/quant4x-taylor-api/monitoring_app", help="Set MT4 main path")

args = parser.parse_args()

mt_path = args.path

def get_first_day_week(dt):
    # This is for getting from an specific date --- Test only ---
    day = '06/04/2022'
    dt = datetime.strptime(day, '%d/%m/%Y')

    # This is to get from the actual date -- Prod ---
    # dt = datetime.today()

    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=6)

    print(start)
    print(end)

    return start


def read_file(path):
    try:
        f = open(path, "r")

        data = json.load(f)

        day = '06/04/2022'
        dt = datetime.strptime(day, '%d/%m/%Y')

        first_day_week = get_first_day_week(dt)

        transactions = 0
        deposits = 0.0
        prior_profit = 0.0
        current_profit = 0.0

        for i in data['transactions']:
            # print(i)
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

        print(transactions)
        print(deposits)
        print(prior_profit)
        print(current_profit)
        # print(data["kpi"]["balance"])

    except:
        print("Failure on opening a file")


def search_files():
    try:
        while True:
            for (dir_path, dir_names, file_names) in walk(mt_path):
                # for windows
                # path_to_check = dir_path+"\\track_taylor.txt"

                # for mac
                path_to_check = dir_path+"/track_taylor.txt"

                if path.exists(path_to_check):
                    read_file(path_to_check)

            time.sleep(10.0)

    except KeyboardInterrupt:
        print("Program finished by user.")
        pass


if __name__ == "__main__":
    search_files()
