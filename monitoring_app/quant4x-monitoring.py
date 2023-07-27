import argparse
import json
import logging
import tkinter as tk
import datetime
import psycopg2
import psycopg2.extras

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

window = tk.Tk()

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
    try:
        sql = f"""INSERT INTO accounts(
                    id,
                    balance, 
                    drawdown, 
                    equity, 
                    product_name, 
                    profit_loss)
                    VALUES (
                        '{account['mt_account_id']}',  
                        '{account["kpi"]["balance"]}', 
                        '{account["kpi"]["drawn_down"]}', 
                        '{account["kpi"]["equity"]}', 
                        '{account["info"]["product_name"]}', 
                        '{account['current_profit']}'
                        ) ON CONFLICT ON CONSTRAINT accounts_pkey DO
                    UPDATE 
                       SET 
                           balance='{account["kpi"]["balance"]}', 
                           drawdown='{account["kpi"]["drawn_down"]}', 
                           equity='{account["kpi"]["equity"]}', 
                           product_name='{account["info"]["product_name"]}', 
                           profit_loss='{account['current_profit']}';"""

        cursor.execute(sql)

        conn.commit()

    except Exception as error:
        print ("Oops! An exception has occured:", error)
        print ("Exception TYPE:", type(error))
        return None

def add_position(account_id, position):
    try:
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
                    type)
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
                        '{position["type"]}');"""
        
        cursor.execute(sql)

        conn.commit()

    except:
        return None


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

        account_id = data['mt_account_id']

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

        id = account_id
        data["current_profit"] = current_profit
        fmt_first_day = first_day_week.strftime("%m_%d_%Y")
        fmt_last_day = last_day_week.strftime("%m_%d_%Y")

        date_scope = f"{data['mt_account_id']}-{fmt_first_day}-{fmt_last_day}"

        print( f"Account: {id} | date signature: {date_scope}" )

        add_or_update_account(data)

    except ValueError:
        print("Failure on opening a file")


def search_files():
    try:
        # while True:
        for (dir_path, dir_names, file_names) in walk(mt_path):
            # for windows
            path_to_check = dir_path+"\\track_taylor.txt"

            # print(f"File {path_to_check}")

            if path.exists(path_to_check) == True:
                read_file(path_to_check)

            # time.sleep(60.0)

    except KeyboardInterrupt:
        print("Program finished by user.")
        pass

def update_dashboard(title_label):

    try:
        print("Searching file")

        search_files()
        
    except Exception as e:
        logging.critical(e, exc_info=True)  # log exception info at CRITICAL log level
        search_files()
        pass

    # Schedule the next update after 1 second (1000 milliseconds)

    current_time = datetime.now()
    time_string = current_time.strftime("%H:%M:%S")  # Format as HH:MM:SS

    title_label.configure(text=time_string)

    window.after(5000, update_dashboard, title_label)

def create_app():
    window.title("Quant4x Monitoring")
    window.configure(width=800, height=600)
    window.configure(bg='lightgray')

    # move window center
    winWidth = window.winfo_reqwidth()
    winwHeight = window.winfo_reqheight()
    posRight = int(window.winfo_screenwidth() / 2 - winWidth / 2)
    posDown = int(window.winfo_screenheight() / 2 - winwHeight / 2)
    window.geometry("+{}+{}".format(posRight, posDown))

    # Create a title label
    title_label = tk.Label(window, text="Cool Dashboard", font=("Arial", 14))
    title_label.pack(pady=20)

    print("Dash Started")

    update_dashboard(title_label)

    window.mainloop()

if __name__ == "__main__":
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
    except:
        print("APP FAILED")
        create_app()
        

    