import argparse
import json
import datetime
import psycopg2
import psycopg2.extras

import time

# command to create one executable file
# PyInstaller --onefile quant4x-monitoring.py

from os import walk
from os import path
from datetime import datetime, timedelta

parser = argparse.ArgumentParser()

# for windows
parser.add_argument("-p", "--path", default="C:\\Users\\Extreme PC\\Documents\\node\\quant4x-dashboard\\python", help="Set MT4 main path")

args = parser.parse_args()

mt_path = args.path

print(f"MT4 Path: {mt_path}")

conn = None
cursor = None

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

def add_or_update_account(account):
    
    sql = f"""INSERT INTO accounts(
                id,
                trades,
                balance,
                drawdown, 
                equity, 
                product_name, 
                profit_loss)
                VALUES (
                    '{account['mt_account_id']}',  
                    '{account["trades"]}', 
                    '{account["kpi"]["balance"]}', 
                    '{account["kpi"]["drawn_down"]}', 
                    '{account["kpi"]["equity"]}', 
                    '{account["info"]["product_name"]}', 
                    '{account['current_profit']}'
                    ) ON CONFLICT ON CONSTRAINT accounts_pkey DO
                UPDATE 
                    SET 
                        updated_at='now()',
                        trades='{account["trades"]}',
                        balance='{account["kpi"]["balance"]}', 
                        drawdown='{account["kpi"]["drawn_down"]}', 
                        equity='{account["kpi"]["equity"]}', 
                        product_name='{account["info"]["product_name"]}', 
                        profit_loss='{account['current_profit']}';"""

    cursor.execute(sql)

    conn.commit()

def add_position(account_id, position):

    sql = f"""INSERT INTO public.positions(
                account_id, 
                ticket, 
                close_price, 
                close_time, 
                commission, 
                profit, 
                size, 
                swap, 
                symbol, 
                type,
                updated_at)
                VALUES (
                    '{account_id}', 
                    '{position["ticket"]}', 
                    '{position["close_price"]}',
                    '{position["close_time"]}', 
                    '{position["commission"]}',
                    '{position["profit"]}',
                    '{position["size"]}',
                    '{position["swap"]}', 
                    '{position["symbol"]}', 
                    '{position["type"]}',
                    'now()')
                ON CONFLICT ON CONSTRAINT positions_pkey DO
                    UPDATE 
                        SET 
                            updated_at='now()';"""
    
    cursor.execute(sql)

    conn.commit()

def add_symbol(account_id, symbol):

    sql = f"""INSERT INTO public.symbols(
                account_id, 
                symbol, 
                trades,
                updated_at)
                VALUES (
                    '{account_id}', 
                    '{symbol["symbol"]}', 
                    '{symbol["trades"]}',
                    'now()')
                ON CONFLICT ON CONSTRAINT symbols_pkey DO
                    UPDATE 
                        SET 
                            trades = '{symbol["trades"]}',
                            updated_at = 'now()';"""
    
    cursor.execute(sql)

    conn.commit()


def read_file(path):

    f = open(path, "r")

    data = json.load(f)

    dt = datetime.today()

    first_day_week = get_first_day_week(dt)
    last_day_week = get_last_day_week(dt)

    transactions = 0
    deposits = 0.0
    prior_profit = 0.0
    current_profit = 0.0

    account_id = data['mt_account_id']

    if "transactions" in data:
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

            add_position(account_id, i)

    if "symbols" in data:
        for i in data['symbols']:
            add_symbol(account_id, i)

    id = account_id
    data["current_profit"] = current_profit
    fmt_first_day = first_day_week.strftime("%m_%d_%Y")
    fmt_last_day = last_day_week.strftime("%m_%d_%Y")

    trades = data["trades"]

    date_scope = f"{data['mt_account_id']}-{fmt_first_day}-{fmt_last_day}"

    print( f"Account: {id} | date signature: {date_scope} | trades: {trades}" )

    add_or_update_account(data)


def search_files():

    # while True:
    for (dir_path, dir_names, file_names) in walk(mt_path):
        # for windows
        path_to_check = dir_path+"\\track_taylor.txt"

        if path.exists(path_to_check) == True:
            read_file(path_to_check)
        
def create_app():
    # while True:
    current_time = datetime.now()
    time_string = current_time.strftime("%H:%M:%S")  # Format as HH:MM:SS
    
    print(f"Execution Time: {time_string}" )
    
    search_files()
    time.sleep(60)

if __name__ == "__main__":

    if conn == None:

        conn = psycopg2.connect(database="defaultdb",
                        host="quant4x-admin-database-do-user-3044858-0.b.db.ondigitalocean.com",
                        user="doadmin",
                        password="AVNS_KmHOAPDB_osaTG-XvN9",
                        port="25060")
        
        conn.autocommit = True

    # to test
    # read_file("track_taylor.txt")
    # pass

    cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    try:
        create_app()
    except Exception as e:
        print(f"APP FAILED - {e}")
        # create_app()
    except KeyboardInterrupt:
        print("Program finished by user.")
    pass

    if conn != None:
        conn.close()
        

    