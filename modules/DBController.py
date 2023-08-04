import psycopg2
import psycopg2.extras
import requests
from datetime import datetime, timedelta

from modules import Talk

class DBController:

    conn = None

    talk = Talk()

    latest_telegram_message_read = ""

    telegram_bot_name = "@taylor_capital_ai_bot"
    telegram_bot_token = "6472164866:AAGWkjcO3vcQDomz0wd3Lf6uoJZlgRrM_8E"
    # The Taylor's official chat_id = -1001712753849
    # The Taylor's Group performance report chat_id = -1001755698269
    telegram_chat_id = "-1001712753849"

    def get_client_by_code(self, code, is_scope_report = False, start_date = None, end_date = None):

        if start_date is None or end_date is None:
            dt = datetime.today()
            start_date = self.get_first_day_week(dt)
            end_date = self.get_last_day_week(dt)

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"SELECT * FROM clients AS cli WHERE cli.code = {code}")

        client = cursor.fetchone()

        cursor.close()

        client_dict = {}

        client_dict["code"] = client["code"]
        client_dict["name"] = client["name"]
        client_dict["week_balance"] = float(client["week_balance"])
        client_dict["week_profit_loss"] = float(client["week_profit_loss"])
        client_dict["week_profit_percent"] = float(client["week_profit_percent"])

        client_dict["accounts"] = self.get_accounts(client["code"])

        client_dict["scope_profit"] = 0.0
        client_dict["scope_transactions"] = 0
        client_dict["scope_profit_percent"] = 0

        for account in client_dict["accounts"]:

            if "id" in account:
                account["kpis"] = self.get_positions_kpis(account["id"], start_date, end_date)
                account["kpis"]["percent"] = round((account["kpis"]["profit_loss"]/(abs(account["balance"])+abs(account["kpis"]["profit_loss"]))) * 100, 2)

                client_dict["scope_profit"] += account["kpis"]["profit_loss"]
                client_dict["scope_transactions"] += account["kpis"]["transactions"]
                client_dict["scope_profit_percent"] = round((client_dict["scope_profit"]/(abs(client_dict["week_balance"])+abs(client_dict["scope_profit"]))) * 100, 2)

        return client_dict
        
    # def get_client_accounts_by_code(self, code):

    #     cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    #     cursor.execute(f"SELECT * FROM clients AS cli INNER JOIN accounts AS acc ON acc.client_code = cli.code WHERE cli.code = {code}")

    #     cursor_result = cursor.fetchone()

    #     cursor.close()

    #     if cursor_result == None:
    #         return None
    #     else:
    #         return cursor_result
        
    def set_user_code(self, email, code):

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        sql = f"UPDATE users SET code = '{code}' WHERE email = '{email}'"
        
        cursor.execute(sql)

        self.conn.commit()

        cursor.close()
        
        return ""
    
    def get_first_day_week(self, dt):
        dt = datetime.today()

        start = dt - timedelta(days=dt.weekday()+1)

        return start
    
    def get_last_day_week(self, dt):
        dt = datetime.today()

        start = dt - timedelta(days=dt.weekday()+1)
        end = start + timedelta(days=5)

        return end
    
    def get_accounts(self, code):
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""SELECT distinct(account_id) FROM accounts acc 
		                        INNER JOIN clients_accounts cli_acc ON cli_acc.client_code = {code};""")

        cursor_result = cursor.fetchall()

        cursor.close()

        accounts = []

        for result in cursor_result:
            account = self.get_account(result["account_id"])
            accounts.append(account)

        return accounts
    
    def get_symbols(self, id):
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""SELECT * FROM symbols where account_id = '{id}';""")

        cursor_result = cursor.fetchall()

        cursor.close()

        symbols = []

        for symbol in cursor_result:
            symbol = {"symbol": symbol["symbol"], "trades": int(symbol["trades"])}
            symbols.append(symbol)
            
        return symbols
        
    def get_account(self, id):
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""SELECT * FROM accounts where id = '{id}';""")

        cursor_result = cursor.fetchone()

        cursor.close()

        account = {}

        if cursor_result != None:

            account["id"] = cursor_result["id"]
            account["balance"] = float(cursor_result["balance"])
            account["drawdown"] = float(cursor_result["drawdown"])
            account["equity"] = float(cursor_result["equity"])
            account["trades"] = float(cursor_result["trades"])
            account["product_name"] = cursor_result["product_name"]
            account["profit_loss"] = float(cursor_result["profit_loss"])
            account["symbols"] = self.get_symbols(account["id"])
        else:
            print(f"AN ACCOUNT ID WAS NOT FOUND IN DETAIL: {id}")
            
        return account
    
    def get_clients(self, is_scope_report = False, start_date = None, end_date = None):

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"SELECT * FROM clients")

        cursor_result = cursor.fetchall()

        cursor.close()

        clients = []

        for client in cursor_result:
            client_dict = self.get_client_by_code(client["code"], is_scope_report, start_date, end_date)
            clients.append(client_dict)

        return clients
    
    def get_positions_kpis(self, account_id, start_date, end_date):
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""SELECT sum(profit) as profit_loss, count(ticket) as transactions FROM positions pos
                                WHERE pos.account_id = '{account_id}' 
                                    AND pos.close_time > TO_TIMESTAMP('{start_date}','DD/MM/YYYY')
                                    AND pos.close_time < TO_TIMESTAMP('{end_date}','DD/MM/YYYY')
                                    AND pos.type != 6;""")

        cursor_result = cursor.fetchone()

        cursor.close()

        kpi = {}

        if cursor_result != None:
            if cursor_result["profit_loss"] == None or cursor_result["transactions"] == None:

                kpi["profit_loss"] = 0.0
                kpi["transactions"] = 0.0

                return kpi
            
            kpi["profit_loss"] = float(cursor_result["profit_loss"])
            kpi["transactions"] = int(cursor_result["transactions"])

        return kpi
        
    def update_accounts_kpi(self):

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT * FROM clients;
                    """)
        
        clients_result = cursor.fetchall()

        cursor.close()

        clients_codes = []

        for client in clients_result:
            client_code = {"code": client["code"], "week_profit_loss": client["week_profit_loss"], "week_balance": client["week_balance"]}
            clients_codes.append(client_code)

        for client_code in clients_codes:

            client_code_code = client_code["code"]
            client_code_week_profit_loss = client_code["week_profit_loss"]
            client_code_week_balance = client_code["week_balance"]

            cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

            cursor.execute(f"""
                            SELECT * FROM accounts as acc
                            INNER JOIN clients_accounts cli_acc 
                                ON cli_acc.account_id = acc.id
                                AND cli_acc.client_code = {client_code_code};
                        """)

            cursor_result = cursor.fetchall()

            cursor.close()

            week_profit_loss = 0.0
            week_balance = 0.0

            for account in cursor_result:
                week_profit_loss += float(account["profit_loss"])
                week_balance += float(account["balance"])

            if week_balance != 0.0 and week_profit_loss != 0.0:
                week_profit_percent = round((week_profit_loss/(abs(week_balance)+abs(week_profit_loss))) * 100, 2)
            else:
                week_profit_percent = 0.0

            cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

            sql = f"""UPDATE clients 
                    SET week_balance = '{week_balance}', 
                    week_profit_loss = '{week_profit_loss}',
                    week_profit_percent = '{week_profit_percent}'
                    WHERE code = '{client_code_code}'"""
            
            cursor.execute(sql)

            self.conn.commit()

            cursor.close()

            # SEND MESSAGE TO TELEGRAM IF PROFIT CHANGED
            if week_balance != client_code_week_balance:
                
                if client_code_code == 1:
                    # self.send_message_to_telegram(client_code_code, week_profit_loss, week_profit_percent)
                    difference = round(float(week_balance) - float(client_code_week_balance),2)
                    difference_in_percent = round((difference/(abs(float(client_code_week_balance))+abs(difference))) * 100, 2)

                    if difference_in_percent > 0:
                        # message_to_send = f"""--Taylor Update--\n🟢 ${round(difference),2} ( {difference_in_percent}% )\n💰 Total balance: ${round(week_balance,2)}"""
                        # message_to_send = f"""🟢 ${difference} - 💰Total balance: ${round(week_balance,2)}"""
                        # self.send_telegram_message(message_to_send)

                        question = f"""Please keep the emojis to make it looking cool and make a very short joke in context with the message at end. 
                        May you create a message presenting the numbers in the first person of the pronoun with max 50 characters? 
                        🟢 Total earned with the trade was +${difference} 💰 After this gain the current Taylor's balance is: ${round(week_balance,2)}"""

                        self.taylor_says_telegram(question)
                        
                    elif difference_in_percent < 0:
                        # message_to_send = f"""--Taylor Update--\n🔴 -${round(difference,2)} ( -{difference_in_percent}% )\n💰 Total balance: ${round(week_balance,2)}"""
                        # message_to_send = f"""🔴 -${difference} - 💰Total balance: ${round(week_balance,2)}"""
                        # self.send_telegram_message(message_to_send)

                        question = f"""Please keep the emojis. There is nothing positive about the balance when there is a loss in the capital. May you create a message, presenting the numbers in the first person of the pronoun with max 50 characters? 
                        🔴 Total earned with the trade was -${difference} 💰 After this loss the current Taylor's balance is: ${round(week_balance,2)}"""

                        self.taylor_says_telegram(question)

        return ""
    
    def get_bot_message_from_group(self):

        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/getUpdates"

        response = requests.get(url)

        response_json = response.json()

        if len( response_json["result"] ) == 0:
            return ""

        messages_filtered_by_chat_id = []

        for result in response_json["result"]:
            
            if "message" in result:
                if str(result["message"]["chat"]["id"]) == self.telegram_chat_id:
                    messages_filtered_by_chat_id.append(result["message"])

        latest_result = messages_filtered_by_chat_id[-1]

        text = latest_result["text"]

        if self.latest_telegram_message_read == text:
            return ""
    
        self.latest_telegram_message_read = text

        if text.find(f"{self.telegram_bot_name}") >= 0:
            
            talk_response = self.taylor_says_telegram(text)

            return talk_response

        return ""

    def taylor_says_telegram(self, message):

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT * FROM ai_controller WHERE channel = 'telegram';
                    """)
        
        cursor_result = cursor.fetchone()

        cursor.close()

        if cursor_result["is_active"] == False:
            return ""
        
        self.talk.prepare_on_demand_prompt( self.get_performance_by_code(1) )
        talk_response = self.talk.get_response(message)

        self.send_telegram_message(talk_response)
    
        return talk_response
    
    def send_telegram_message(self, message):
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage?chat_id={self.telegram_chat_id}&text={message}"

        x = requests.get(url)
        return x.status_code

    def get_profit_percentage_by_code(self, code):
        
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT id, balance, drawdown, equity, product_name, profit_loss, trades FROM accounts as acc
                        INNER JOIN clients_accounts cli_acc 
                            ON cli_acc.account_id = acc.id
                            AND cli_acc.client_code = {code};
                    """)

        cursor_result = cursor.fetchall()

        cursor.close()

        profit_loss = 0.0
        balance = 0.0

        for account in cursor_result:
            profit_loss += float(account["profit_loss"])
            balance += float(account["balance"])

        if profit_loss != 0 and balance != 0:
            total_profit_percent = round((profit_loss/(abs(balance)+abs(profit_loss))) * 100, 2)
        else:
            total_profit_percent = 0

        return total_profit_percent
    
    def get_internal_performance_by_code(self, code):        

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""

                        SELECT id, balance, drawdown, equity, product_name, profit_loss, trades 
                        FROM accounts as acc
                        INNER JOIN clients_accounts cli_acc 
                            ON cli_acc.account_id = acc.id
                            AND cli_acc.client_code = {code};

                    """)

        cursor_result = cursor.fetchall()

        cursor.close()

        if cursor_result == None:
            return None
        else:
            return cursor_result
        
        
    def get_performance_by_code(self, code):        

        dt = datetime.today()
        first_day_week = self.get_first_day_week(dt)
        last_day_week = self.get_last_day_week(dt)

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""

                        SELECT id, balance, drawdown, equity, product_name, profit_loss, trades FROM accounts as acc
                        INNER JOIN clients_accounts cli_acc 
                            ON cli_acc.account_id = acc.id
                            AND cli_acc.client_code = {code};

                    """)

        cursor_result = cursor.fetchall()

        cursor.close()

        return_object = {}

        return_object['is_live'] = self.get_is_live(first_day_week, last_day_week)
        return_object['products'] = cursor_result

        if return_object == None:
            return None
        else:
            return return_object
        
    def get_is_live(self, first_day_week, last_day_week):
        now_est = datetime.now()
        
        first_day_week_adjusted = first_day_week.replace(hour=20, minute=00)
        last_day_week_adjusted = last_day_week.replace(hour=22, minute=00)
        
        if now_est > first_day_week_adjusted and now_est < last_day_week_adjusted:
            return True
        else:
            return False

    def __init__(self, *args, **kwargs):

        self.conn = psycopg2.connect(database="defaultdb",
                        host="quant4x-admin-database-do-user-3044858-0.b.db.ondigitalocean.com",
                        user="doadmin",
                        password="AVNS_KmHOAPDB_osaTG-XvN9",
                        port="25060")
        
        self.conn.autocommit = True

        super().__init__(*args, **kwargs)