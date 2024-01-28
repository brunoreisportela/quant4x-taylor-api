import psycopg2
import psycopg2.extras
import requests
from datetime import datetime, timedelta
import simplejson as json
import uuid 
import re

from modules import Talk
from modules import MayTapi

class DBController:

    conn = None

    talk = Talk()
    maytapi = MayTapi()

    latest_telegram_message_read = ""

    telegram_bot_name = "@taylor_capital_ai_bot"
    telegram_bot_token = "6472164866:AAGWkjcO3vcQDomz0wd3Lf6uoJZlgRrM_8E"
    # The Taylor's official chat_id = -1001712753849
    # The Taylor's Group performance report chat_id = -1001755698269
    telegram_chat_id = "-1001712753849"

    def send_whatsapp_message(self, payload):
        self.maytapi.send_message(payload)

    def standardize_phone_number(self, number):
        cleaned_number = re.sub(r'(?<!^)\D', '', number)

        # Ensure the number starts with '+'
        if not cleaned_number.startswith('+'):
            cleaned_number = '+' + cleaned_number

        return cleaned_number

    def dateToString(self, date):
        formatted_date = date.strftime("%d/%m/%Y")
        return formatted_date
    

    def stringToDate(self, date_str):
        # Convert the input string to a datetime object
        date_object = datetime.strptime(date_str, "%d/%m/%Y")  # Adjust the format based on your input string format

        # Convert the date to a string in the desired format
        formatted_date = date_object.strftime("%d/%m/%Y")
        return formatted_date
    
    def get_cluster_data(self, cluster_id, client_code):
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT *,
                            MIN(float_dd_percent) OVER (ORDER BY updated_at ASC) AS "min",
                            MAX(float_dd_percent) OVER (ORDER BY updated_at ASC) AS "max"
                        FROM (
                            SELECT *
                            FROM cluster_kpis AS clu_kpi
                            INNER JOIN clusters clu ON clu_kpi.cluster_id = '{cluster_id}'
                                AND clu_kpi.client_code = {client_code}
                            ORDER BY updated_at DESC
                            LIMIT 80
                        ) AS t
                        ORDER BY updated_at ASC;
                       """)

        cursor_result = cursor.fetchall()

        cursor.close()
        

        cluster_data = []

        for result in cursor_result:
            cluster = {}

            cluster["token"] = result["token"]
            cluster["take_profit"] = float(result["take_profit"])
            cluster["stop_loss"] = float(result["stop_loss"])
            cluster["description"] = result["description"]
            cluster["float_dd_percent"] = float(result["float_dd_percent"])

            cluster["min"] = float(result["min"])
            cluster["max"] = float(result["max"])

            cluster["day"] = result["day"]
            cluster["month"] = result["month"]
            cluster["year"] = result["year"]
            cluster["hour"] = result["hour"]
            cluster["minute"] = result["minute"]

            cluster_data.append(cluster)

        return cluster_data

    def get_client_by_code(self, code, start_date = None, end_date = None, weeks_limit = 0, load_accounts = True, load_clusters = True):

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
        client_dict["is_active"] = client["is_active"]

        if load_clusters:
            client_dict["clusters"] = self.get_clusters_per_client(client["code"])

            for (i, cluster) in enumerate(client_dict["clusters"]):
                data = self.get_cluster_data(cluster["cluster_id"], client_dict["code"])
                client_dict["clusters"][i]["data"] = data

        if load_accounts:
            for account in client_dict["accounts"]:
                
                if "id" in account:
                    self.get_weeks_per_account(account, weeks_limit)
                    account["kpis"] = self.get_positions_kpis(account["id"], start_date, end_date)
                    account["kpis"]["percent"] = round((account["kpis"]["profit_loss"]/(abs(account["balance"])+abs(account["kpis"]["profit_loss"]))) * 100, 2)

                    client_dict["scope_profit"] += account["kpis"]["profit_loss"]
                    client_dict["scope_transactions"] += account["kpis"]["transactions"]
                    client_dict["scope_profit_percent"] = round((client_dict["scope_profit"]/(abs(client_dict["week_balance"])+abs(client_dict["scope_profit"]))) * 100, 2)

        return client_dict
    
    def get_positions_summary_until_date(self, account_id, end_date = None):
        
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""SELECT * FROM positions pos
                                WHERE pos.account_id = '{account_id}'
                                    AND pos.close_time <= TO_TIMESTAMP('{end_date}','DD/MM/YYYY')
                        """)

        cursor_result = cursor.fetchall()
        
        cursor.close()

        summary = {}

        profit = 0.0
        commission = 0.0
        swap = 0.0

        for result in cursor_result:
            profit += float(result["profit"])
            commission += float(result["commission"])
            swap += float(result["swap"])

        summary["profit"] = profit
        summary["commission"] = commission
        summary["swap"] = swap
            
        return summary
    
    def get_sentiment_pairs(self):
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""SELECT * FROM sentiment_pairs;""")

        cursor_result = cursor.fetchall()

        cursor.close()

        sentiment_pairs = []

        for result in cursor_result:
            sentiment_pair = {"pair": result["pair"], "sentiment": result["sentiment"]}
            sentiment_pairs.append(sentiment_pair)

        return sentiment_pairs
    
    def save_sentiment_pair(self, pair, sentiment):
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        sql = f"""UPDATE sentiment_pairs SET sentiment = '{sentiment}', updated_at = 'NOW()' WHERE pair = '{pair}'"""
        
        cursor.execute(sql)

        self.conn.commit()

        cursor.close()
        
        return ""

    def get_weeks_per_account(self, account, weeks_limit = 0):

        account_id = account["id"]
        
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""SELECT * FROM positions pos
                                WHERE pos.account_id = '{account_id}'
                                    AND pos.type != 6 order by close_time ASC;""")

        cursor_result = cursor.fetchall()
        
        cursor.close()

        weeks = []

        current_first_day_week = datetime.now()
        current_week = {}
        index = 0

        weeks_total_profit = 0.0
        weeks_total_commission = 0.0
        weeks_total_swap = 0.0

        for result in cursor_result:

            first_day_week = self.get_first_day_week(result["close_time"])

            if first_day_week.date() != current_first_day_week.date():
                current_week = {}
                current_week["index"] = index
                current_week["profit"] = float(result["profit"])
                current_week["commission"] = float(result["commission"])
                current_week["swap"] = float(result["swap"])

                current_week["start_date"] = self.dateToString(first_day_week)
                current_week["end_date"] = self.dateToString(self.get_last_day_week(first_day_week))

                current_first_day_week = first_day_week
                index += 1

                weeks_total_profit += current_week["profit"]
                weeks_total_commission += current_week["commission"]
                weeks_total_swap += current_week["swap"]

                weeks.append(current_week)

            else:
                weeks[len(weeks)-1]["profit"] += float(result["profit"])
                weeks[len(weeks)-1]["commission"] += float(result["commission"])
                weeks[len(weeks)-1]["swap"] += float(result["swap"])

                weeks_total_profit += float(result["profit"])
                weeks_total_commission += float(result["commission"])
                weeks_total_swap += float(result["swap"])

        if weeks_limit > 0:
            account["weeks"] = weeks[-weeks_limit:]
        else:
            account["weeks"] = weeks

        account["weeks_count"] = len(weeks)

        account["weeks_total_profit"] = weeks_total_profit
        account["weeks_total_commission"] = weeks_total_commission
        account["weeks_total_swap"] =  weeks_total_swap

        return account

    def get_current_time_details(self):
        now = datetime.now()

        day = now.day
        month = now.month
        year = now.year
        hour = now.hour
        minute = now.minute

        if minute > 0 and minute < 15:
            minute = 0
        elif minute >= 15 and minute < 30:
            minute = 15
        elif minute >= 30 and minute < 45:
            minute = 30
        elif minute >= 45:
            minute = 45

        return day, month, year, hour, minute

    def set_cluster_KPI(self, cluster_info):
        
        day, month, year, hour, minute = self.get_current_time_details()

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        sql = f"""
                INSERT INTO public.cluster_kpis(
                    client_code, 
                    cluster_id, 
                    float_dd_percent, 
                    day, 
                    month, 
                    year, 
                    hour, 
                    minute
                )
                VALUES (
                    {cluster_info["client_code"]}, 
                    {cluster_info["cluster_id"]}, 
                    {cluster_info["float_dd_percent"]}, 
                    {day}, 
                    {month}, 
                    {year}, 
                    {hour}, 
                    {minute}
                )
                ON CONFLICT ON CONSTRAINT cluster_kpis_pkey DO
                UPDATE 
                    SET 
                        updated_at='now()',
                        float_dd_percent='{cluster_info["float_dd_percent"]}';
                """
        
        cursor.execute(sql)

        self.conn.commit()

        cursor.close()

    def get_week_boundaries(self, current_date):
        # Parse the current date
        date_format = "%Y-%m-%d"
        current_date = datetime.strptime(current_date, date_format)

        # Calculate the Sunday and Friday of the week
        start_of_week = current_date - timedelta(days=current_date.weekday() + 1)
        end_of_week = start_of_week + timedelta(days=5)

        # Prepare the JSON output with separated day, month, and year
        result = {
            "sunday": {
                "day": start_of_week.day,
                "month": start_of_week.month,
                "year": start_of_week.year
            },
            "friday": {
                "day": end_of_week.day,
                "month": end_of_week.month,
                "year": end_of_week.year
            }
        }

        return result
    
    def get_current_day_only_bet_performance(self):
        current_date = datetime.now() # Example current date and time
        next_date = current_date + timedelta(days=1)

        day = next_date.day
        month = next_date.month
        year = next_date.year
        hour = next_date.hour
        minute = next_date.minute

        get_week_boundaries = self.get_week_boundaries(f"{year}-{month}-{day}")

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        query = f"""SELECT SUM(profit_loss) as profit_loss, (SELECT account_bankroll FROM performance WHERE account_id = '8' ORDER BY update_time DESC LIMIT 1) AS balance, CEIL((EXTRACT(EPOCH FROM AGE(TO_DATE(year || '-' || month || '-' || day, 'YYYY-MM-DD'), DATE '2022-12-01')) / 86400) / 7.03) AS cycle FROM performance WHERE account_id = '8' AND (day >= {get_week_boundaries["sunday"]["day"]}) AND (month >= {get_week_boundaries["sunday"]["month"]} and month <= {get_week_boundaries["friday"]["month"]}) AND (year >= {get_week_boundaries["sunday"]["year"]} and year <= {get_week_boundaries["friday"]["year"]}) group by cycle ORDER BY cycle DESC LIMIT 1"""

        cursor.execute(query)

        cursor_result = cursor.fetchone()

        cursor.close()

        if cursor_result == None:
            return 0

        return cursor_result
    
    def get_current_day_performance(self):
        current_date = datetime.now() # Example current date and time
        next_date = current_date + timedelta(days=1)

        day = next_date.day
        month = next_date.month
        year = next_date.year
        hour = next_date.hour
        minute = next_date.minute

        get_week_boundaries = self.get_week_boundaries(f"{year}-{month}-{day}")

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        query = f"""SELECT SUM(profit_loss) as profit_loss, (SELECT account_bankroll FROM performance WHERE account_id = '8' ORDER BY update_time DESC LIMIT 1) AS balance, CEIL((EXTRACT(EPOCH FROM AGE(TO_DATE(year || '-' || month || '-' || day, 'YYYY-MM-DD'), DATE '2022-12-01')) / 86400) / 7.03) AS cycle FROM performance WHERE (day >= {get_week_boundaries["sunday"]["day"]}) AND (month >= {get_week_boundaries["sunday"]["month"]} and month <= {get_week_boundaries["friday"]["month"]}) AND (year >= {get_week_boundaries["sunday"]["year"]} and year <= {get_week_boundaries["friday"]["year"]}) group by cycle ORDER BY cycle DESC LIMIT 1"""

        cursor.execute(query)

        cursor_result = cursor.fetchone()

        cursor.close()

        if cursor_result == None:
            return 0

        return cursor_result

    def add_performance(self, payload):
        
        day, month, year, hour, minute = self.get_current_time_details()

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        if isinstance(payload, str):
            payload = json.loads(payload)

        sql = f"""
                INSERT INTO public.performance(
                    account_id, 
                    reference_id,
                    day, 
                    month, 
                    year, 
                    hour, 
                    minute, 
                    total_bankroll, 
                    account_bankroll, 
                    profit_loss)
                VALUES (
                    '{payload["account_id"]}',
                    '{payload["reference_id"]}',
                    {day},
                    {month},
                    {year},
                    {hour},
                    {minute},
                    {payload["total_bankroll"]},
                    {payload["account_bankroll"]},
                    {payload["profit_loss"]}
                    )
                ON CONFLICT ON CONSTRAINT performance_pkey DO
                UPDATE 
                    SET 
                        update_time='now()',
                        profit_loss='{payload["profit_loss"]}';
                """
        
        cursor.execute(sql)

        self.conn.commit()

        cursor.close()

        return {"row_count": cursor.rowcount}
    
    def set_user_code(self, email, code):

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        sql = f"UPDATE users SET code = '{code}' WHERE email = '{email}'"
        
        cursor.execute(sql)

        self.conn.commit()

        cursor.close()
        
        return ""
    
    def get_first_day_week(self, dt, offset = 1):
        # dt = datetime.today()

        start = dt - timedelta(days=dt.weekday()+offset)

        return start
    
    # def get_last_day_week(self, dt):
    #     # dt = datetime.today()

    #     start = dt - timedelta(days=dt.weekday()+1)
    #     end = start + timedelta(days=5)

    #     return end
    
    def get_last_day_week(self, dt):
        return self.get_first_day_week(dt) + timedelta(days=13)
    
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

            account["week_start_balance"] = float(cursor_result["week_start_balance"])
            account["week_target"] = float(cursor_result["week_target"])
            account["is_live_active"] = cursor_result["is_live_active"]
            
        else:
            print(f"AN ACCOUNT ID WAS NOT FOUND IN DETAIL: {id}")
            
        return account
    
    def get_clients(self, start_date = None, end_date = None):

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"SELECT * FROM clients")

        cursor_result = cursor.fetchall()

        cursor.close()

        clients = []

        start_date_fmt = start_date
        end_date_fmt = end_date

        if start_date is None or end_date is None:
            dt = datetime.today()
            start_date_fmt = self.dateToString(self.get_first_day_week(dt))
            end_date_fmt = self.dateToString(self.get_last_day_week(dt))
        
        for client in cursor_result:
            client_dict = self.get_client_by_code(client["code"], start_date_fmt, end_date_fmt)
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
                        SELECT * FROM ai_controller WHERE channel = 'telegram';
                    """)
        
        cursor_result = cursor.fetchone()

        cursor.close()

        if cursor_result["is_active"] == False:
            return ""

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

                        message = f"""📈🟢 The balance has increased by {difference_in_percent:.2f}%."""
                        # self.send_telegram_message(message)

                    elif difference_in_percent < 0:

                        message = f"""📉🔴 The balance has decreased by {difference_in_percent:.2f}%."""
                        # self.send_telegram_message(message)

                    id = uuid.uuid1() 

                    self.add_performance(
                        {   
                            "account_id": 1, 
                            "reference_id": id, 
                            "total_bankroll": week_balance, 
                            "account_bankroll": week_balance, 
                            "profit_loss": difference
                        }
                    )

        return ""
    
    def get_bot_message_from_group(self):

        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/getUpdates"

        response = requests.get(url)

        response_json = response.json()

        if len( response_json["result"] ) == 0:
            return ""

        messages_filtered_by_chat_id = []

        for result in response_json["result"]:
            
            if "message" in result and "text" in result["message"]:
                if str(result["message"]["chat"]["id"]) == self.telegram_chat_id:

                    if "@taylor_capital_ai_bot" in result["message"]["text"]:
                        messages_filtered_by_chat_id.append(result["message"])

        if len(messages_filtered_by_chat_id) == 0:
            return ""

        latest_result = messages_filtered_by_chat_id[-1]

        text = latest_result["text"]

        if self.latest_telegram_message_read == text:
            return ""
    
        self.latest_telegram_message_read = text

        if text.find(f"{self.telegram_bot_name}") >= 0:
            
            talk_response = self.taylor_says_telegram(text)

            return talk_response

        return self.latest_telegram_message_read
    
    def taylor_get_answer(self, message):        
        dt = datetime.today()
        start_date_fmt = self.dateToString(self.get_first_day_week(dt))
        end_date_fmt = self.dateToString(self.get_last_day_week(dt))

        self.talk.prepare_on_demand_prompt( self.get_client_by_code(1, start_date_fmt, end_date_fmt, 3, load_accounts=False, load_clusters=False) )
        
        talk_response = self.talk.get_response(message)

        return talk_response
    
    def taylor_get_answer_without_context(self, message):        
        talk_response = self.talk.get_response(message, is_context_prompt = False)
        return talk_response

    def taylor_says_telegram(self, message):        
        dt = datetime.today()
        start_date_fmt = self.dateToString(self.get_first_day_week(dt))
        end_date_fmt = self.dateToString(self.get_last_day_week(dt))

        self.talk.prepare_on_demand_prompt( self.get_client_by_code(1, start_date_fmt, end_date_fmt, 3, load_accounts=False, load_clusters=False) )
        talk_response = self.talk.get_response(message)

        self.send_telegram_message(talk_response)
    
        return talk_response
    
    def send_telegram_message(self, message):
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT * FROM ai_controller WHERE channel = 'telegram';
                    """)
        
        cursor_result = cursor.fetchone()

        cursor.close()

        if cursor_result["is_active"] == False:
            return ""

        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage?chat_id={self.telegram_chat_id}&text={message}"

        x = requests.get(url)
        return x.status_code
    
    def get_week_start_balance_by_account_id(self, account_id):
        
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT week_start_balance FROM accounts WHERE id = '{account_id}';
                    """)

        cursor_result = cursor.fetchone()

        cursor.close()

        if cursor_result != None:
            return float(cursor_result["week_start_balance"])
        else:
            print(f"AN ACCOUNT ID WAS NOT FOUND IN DETAIL: {id}")
            return 100000
        
    def get_is_live_active_by_account_id(self, account_id):
        
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT is_live_active FROM accounts WHERE id = '{account_id}';
                    """)

        cursor_result = cursor.fetchone()

        cursor.close()

        if cursor_result != None:
            return cursor_result["is_live_active"]
        else:
            print(f"AN ACCOUNT ID WAS NOT FOUND IN DETAIL: {id}")
            return True
        
    def get_invest_code_by_account_id(self, account_id):
        
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT code FROM clients 
                            INNER JOIN clients_accounts as cli_acc 
                            ON cli_acc.client_code =  clients.code
                            WHERE cli_acc.account_id = '{account_id}';
                    """)

        cursor_result = cursor.fetchone()

        cursor.close()

        if cursor_result != None:
            return cursor_result["code"]
        else:
            print(f"AN ACCOUNT ID WAS NOT FOUND IN DETAIL: {id}")
            return True
        
    def get_week_target_by_account_id(self, account_id):
        
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT week_target FROM accounts WHERE id = '{account_id}';
                    """)

        cursor_result = cursor.fetchone()

        cursor.close()

        if cursor_result != None:
            return float(cursor_result["week_target"])
        else:
            print(f"AN ACCOUNT ID WAS NOT FOUND IN DETAIL: {id}")
            return 1
        
    def get_week_loss_target_by_account_id(self, account_id):
        
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT week_loss_target FROM accounts WHERE id = '{account_id}';
                    """)

        cursor_result = cursor.fetchone()

        cursor.close()

        if cursor_result != None:
            return float(cursor_result["week_loss_target"])
        else:
            print(f"AN ACCOUNT ID WAS NOT FOUND IN DETAIL: {id}")
            return 20
        
    def get_clusters_per_client(self, code):
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT DISTINCT(cluster_id) FROM accounts as acc
                        INNER JOIN clients_accounts cli_acc 
                            ON cli_acc.client_code = {code};
                        """)

        cursor_result = cursor.fetchall()

        cursor.close()   

        clusters = []

        for cluster in cursor_result:
            clusters.append(cluster)

        return clusters

    def check_latest_percent_from_cluster(self, cluster):
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT * FROM cluster_kpis 
                            WHERE client_code = {cluster["client_code"]} AND 
                            cluster_id = {cluster["cluster_id"]} 
                        ORDER BY updated_at DESC LIMIT 1;
                    """)

        cursor_result = cursor.fetchone()

        cursor.close()

        if cursor_result == None:
            return 0.0

        return float(cursor_result["float_dd_percent"])


    def aggregate_float_dd_KPI_per_cluster(self):
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT * FROM clients ORDER BY code ASC;
                    """)

        cursor_result = cursor.fetchall()

        cursor.close()

        clusters_performance = []

        for client in cursor_result:

            clusters = self.get_clusters_per_client( client["code"])
            
            for cluster in clusters:
                cluster_return = {}

                cluster_return["client_code"] = client["code"]
                cluster_return["cluster_id"] = cluster["cluster_id"]
                cluster_return["float_dd_percent"] = self.get_total_dd(client["code"])

                latest_percent = self.check_latest_percent_from_cluster(cluster_return)

                if cluster_return["float_dd_percent"] != latest_percent:
                    self.set_cluster_KPI(cluster_return)
                    
                clusters_performance.append(cluster_return)


        return clusters_performance
    
    def get_total_dd(self, client_code):

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                                SELECT * FROM accounts as acc
                                INNER JOIN clients_accounts cli_acc 
                                    ON cli_acc.account_id = acc.id
                                    AND cli_acc.client_code = {client_code};
                    """)

        cursor_result = cursor.fetchall()

        cursor.close()

        total_dd = 0.0

        for result in cursor_result:
            total_dd += float(result["drawdown"])

        return -total_dd

    
    def get_account_setup(self, account_id):

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                                SELECT client_code FROM clients_accounts AS cli_acc
                                INNER JOIN clients AS cli ON cli.code = cli_acc.client_code
                                AND cli_acc.account_id = '{account_id}';
                    """)

        cursor_result = cursor.fetchone()

        cursor.close()

        if cursor_result["client_code"] == None:
            return None

        int_code  = int(cursor_result["client_code"])
        
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT acc.equity, acc.balance, acc.week_start_balance as start_balance,acc.week_target AS acc_take_profit,
                            acc.week_loss_target AS acc_stop_loss, 
                            acc.is_live_active AS acc_is_live_active,
                            clu.take_profit AS clu_take_profit,
                            clu.stop_loss AS clu_stop_loss 
                        FROM accounts acc 
                        INNER JOIN clusters clu ON clu.token = acc.cluster_token
                        WHERE acc.id = '{account_id}';
                    """)

        cursor_result = cursor.fetchone()

        cursor.close()

        account = cursor_result

        account["equity"] = float(cursor_result["equity"])
        account["balance"] = float(cursor_result["balance"])
        account["start_balance"] = float(cursor_result["start_balance"])
        account["acc_take_profit"] = float(cursor_result["acc_take_profit"])
        account["acc_stop_loss"] = float(cursor_result["acc_stop_loss"])
        account["acc_is_live_active"] = cursor_result["acc_is_live_active"]
        account["clu_take_profit"] = float(cursor_result["clu_take_profit"])
        account["clu_stop_loss"] = float(cursor_result["clu_stop_loss"])

        account["percent"] = self.get_profit_percentage_by_code(int_code)

        return account

    def get_profit_percentage_by_code(self, code, cluster_id = 1):
        
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT id, balance, drawdown, equity, product_name, profit_loss, week_start_balance, trades FROM accounts as acc
                        INNER JOIN clients_accounts cli_acc 
                            ON cli_acc.account_id = acc.id
                            AND cli_acc.client_code = {code} AND acc.cluster_id = {cluster_id};
                    """)

        cursor_result = cursor.fetchall()

        cursor.close()

        balance = 0.0
        equity = 0.0
        start_balance = 0.0

        for account in cursor_result:
            equity += float(account["equity"])
            balance += float(account["week_start_balance"])
            start_balance += float(account["week_start_balance"])

        dd = self.get_drawdown_by_vars(equity, balance)

        return dd
    
    
    def get_json_setup(self, account_id):
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT j.code, j.name, j.account_id, j.tp as o_tp, j.sl as o_sl, 
                                    j.product_id, prod.tp, prod.sl,
                                    prod.name as product_name,
                                    j.week_start_balance,
                                    j.segment_balance,
                                    prod.lot_ratio,
                                    is_live_active as is_active,
									
									(SELECT 
                                        CASE 
                                            WHEN NOW() - updated_at < INTERVAL '2 hours' THEN sentiment 
                                            ELSE 'mixed' 
                                        END 
                                    FROM sentiment_pairs 
                                    WHERE pair = 'GBPUSD') AS GBPUSD,

                                    (SELECT 
                                        CASE 
                                            WHEN NOW() - updated_at < INTERVAL '2 hours' THEN sentiment 
                                            ELSE 'mixed' 
                                        END 
                                    FROM sentiment_pairs 
                                    WHERE pair = 'EURUSD') AS EURUSD,

                                    (SELECT 
                                        CASE 
                                            WHEN NOW() - updated_at < INTERVAL '2 hours' THEN sentiment 
                                            ELSE 'mixed' 
                                        END 
                                    FROM sentiment_pairs 
                                    WHERE pair = 'USDJPY') AS USDJPY,

                                    (SELECT 
                                        CASE 
                                            WHEN NOW() - updated_at < INTERVAL '2 hours' THEN sentiment 
                                            ELSE 'mixed' 
                                        END 
                                    FROM sentiment_pairs 
                                    WHERE pair = 'USDCAD') AS USDCAD,

                                    (SELECT 
                                        CASE 
                                            WHEN NOW() - updated_at < INTERVAL '2 hours' THEN sentiment 
                                            ELSE 'mixed' 
                                        END 
                                    FROM sentiment_pairs 
                                    WHERE pair = 'GOLD') AS GOLD,

                                    (SELECT 
                                        CASE 
                                            WHEN NOW() - updated_at < INTERVAL '2 hours' THEN sentiment 
                                            ELSE 'mixed' 
                                        END 
                                    FROM sentiment_pairs 
                                    WHERE pair = 'SP500') AS SP500
									FROM (
                                        SELECT * FROM clients as cli
                                        INNER JOIN clients_accounts as cli_acc
                                            ON cli_acc.client_code = cli.code
                                        INNER JOIN accounts as acc
                                            ON cli_acc.account_id = acc.id 
                                        WHERE acc.id = '{account_id}'
                                    ) as j
                                    INNER JOIN products prod
                                    ON prod.id = product_id;
                    """)
        

        cursor_result = cursor.fetchone()

        cursor.close()

        setup_object = {}

        if cursor_result != None:
            setup_object["code"] = cursor_result["code"]
            setup_object["name"] = cursor_result["name"]
            setup_object["product_name"] = cursor_result["product_name"]
            setup_object["account_id"] = cursor_result["account_id"]
            setup_object["o_tp"] = float(cursor_result["o_tp"])
            setup_object["o_sl"] = float(cursor_result["o_sl"])
            setup_object["product_id"] = cursor_result["product_id"]
            setup_object["tp"] = float(cursor_result["tp"])
            setup_object["sl"] = float(cursor_result["sl"])
            setup_object["lot_ratio"] = float(cursor_result["lot_ratio"])
            setup_object["is_active"] = cursor_result["is_active"]
            setup_object["start_balance"] = float(cursor_result["week_start_balance"])
            setup_object["segment_balance"] = float(cursor_result["segment_balance"])
            setup_object["GBPUSD"] = cursor_result["gbpusd"]
            setup_object["EURUSD"] = cursor_result["eurusd"]
            setup_object["USDCAD"] = cursor_result["usdcad"]
            setup_object["USDJPY"] = cursor_result["usdjpy"]
            setup_object["GOLD"] = cursor_result["gold"]
            setup_object["SP500"] = cursor_result["sp500"]

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        cursor.execute(f"""
                        SELECT SUM(equity) as total_equity, 
                               SUM(week_start_balance) as total_balance, 
                               SUM(balance) as reserve_balance FROM accounts as acc
                        INNER JOIN clients_accounts cli_acc 
                            ON cli_acc.account_id = acc.id
                            AND cli_acc.client_code = {setup_object["code"]};
                    """)
        

        cursor_result = cursor.fetchone()

        cursor.close()

        if cursor_result != None:
            setup_object["total_equity"] = float(cursor_result["total_equity"])
            setup_object["total_balance"] = float(cursor_result["total_balance"])
            setup_object["reserve_balance"] = float(cursor_result["reserve_balance"])

            setup_object["o_profit"] = self.get_drawdown_by_vars(setup_object["total_equity"], setup_object["total_balance"])
            
            balance_to_use = setup_object["total_balance"]

            if balance_to_use == 0:
                balance_to_use = setup_object["reserve_balance"]

            setup_object["dd"] = self.get_drawdown_by_vars(setup_object["total_equity"], balance_to_use)
        else:
            setup_object["total_equity"] = 0.0
            setup_object["total_balance"] = 0.0
            setup_object["o_profit"] = 0.0
            setup_object["is_active"] = False
            setup_object["reserve_balance"] = 0.0

        return setup_object
    
    def get_drawdown_by_vars(self, equity, balance):
        
        dd = 0

        if equity != 0 and balance != 0:
            dd = round(((equity-balance) * 100) / balance, 2) 

        return dd
    
    def get_float_balance_by_vars(self, equity, balance ):
        
        fbalance = 0

        if equity != 0 and balance != 0:
            if equity > 0:
                fbalance = round((equity-balance), 2)
            else:
                fbalance = round((balance-equity), 2)    

        return fbalance

    def get_performance_by_code(self, code):        

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""

                        SELECT id, balance, drawdown, week_start_balance, equity, product_name, profit_loss, trades 
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
    
    def send_push_broadcast(self, current_day_performance):
        url = "https://prod-taylor-reborn-service-lui32.ondigitalocean.app/active-users-with-push-token"

        x = requests.get(url)

        if x.status_code != 200:
            return x.status_code
        
        users = x.json()

        for user in users:
            
            if "activePercentage" in user:
                if float(user["activePercentage"]) > 0:
                    email = user["email"]
                    active_percentage = float(user["activePercentage"])
                    proportional_profit_loss = round(float(current_day_performance["profit_loss"]) * active_percentage, 2)

                    message = ""
                    profit_loss = 0
                    cycle = 0

                    if proportional_profit_loss != 0:

                        if "profit_loss" in current_day_performance:
                            profit_loss = float(current_day_performance["profit_loss"])

                        if "cycle" in current_day_performance:
                            cycle = int(current_day_performance["cycle"])

                        title = "Float Weekly Result"

                        if profit_loss > 0:
                            message = f"📈 Your Accumulated Result - Cycle {cycle}: +${proportional_profit_loss:.2f} Note: This is a preliminary result, subject to change until the end of the cycle."
                        elif profit_loss < 0:
                            message = f"📉Your Accumulated result - Cycle {cycle}: -${proportional_profit_loss:.2f} Note: This is a preliminary result, subject to change until the end of the cycle."

                        # message_payload = {"to_number": phone_number,"type": "text","message": message}
                        message_payload = {"title": title,"email": email, "message": message}

                        try:
                            self.send_push_notification(message_payload)
                        except Exception as e:
                            print(e)
                            print(message_payload)
                            continue

                    print(proportional_profit_loss)

        return x.status_code
    
    def send_push_notification(self, payload):

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'c5c917655b6d0ax008ssd2d92026f772'
        }

        url = "https://prod-taylor-reborn-service-lui32.ondigitalocean.app/send-push-notification"

        x = requests.post(url, json=payload, headers=headers)

        if x.status_code != 200:
            return x.status_code
        
        return x.status_code

    def send_whatsapp_broadcast(self, current_day_performance):
        url = "https://reborn.taylor.capital/active-users-with-phone-numbers"

        x = requests.get(url)

        if x.status_code != 200:
            return x.status_code
        
        users = x.json()

        for user in users:
            
            if "activePercentage" in user and "phoneNumber" in user and "whatsappTransaction" in user:
                # if user["whatsappTransaction"] == True:
                if len(user["phoneNumber"]) > 0:
                    phone_number = self.standardize_phone_number(user["phoneNumber"])
                    active_percentage = float(user["activePercentage"])
                    proportional_profit_loss = round(float(current_day_performance["profit_loss"]) * active_percentage, 2)

                    message = ""
                    profit_loss = 0
                    cycle = 0

                    if proportional_profit_loss != 0:

                        if "profit_loss" in current_day_performance:
                            profit_loss = float(current_day_performance["profit_loss"])

                        if "cycle" in current_day_performance:
                            cycle = int(current_day_performance["cycle"])

                        if profit_loss > 0:
                            message = f"📈 Your Accumulated Result - Cycle {cycle}: *+${proportional_profit_loss:.2f}* _Note: This is a preliminary result, subject to change until the end of the cycle._"
                        elif profit_loss < 0:
                            message = f"📉Your Accumulated result - Cycle {cycle}: *-${proportional_profit_loss:.2f}* _Note: This is a preliminary result, subject to change until the end of the cycle._"

                        if profit_loss != 0.00:
                            message_payload = {"to_number": phone_number,"type": "text","message": message}
                            # message_payload = {"to_number": "+14389215001","type": "text","message": message}

                            try:
                                self.send_whatsapp_message(message_payload)
                            except Exception as e:
                                print(e)
                                print(message_payload)
                                continue

                    print(proportional_profit_loss)

        return x.status_code
        
    def get_platform_performance(self, code):        

        dt = datetime.today()
        first_day_week = self.get_first_day_week(dt)
        last_day_week = self.get_last_day_week(dt)

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""

                        SELECT id, balance, drawdown, equity, week_start_balance, product_name, profit_loss, trades FROM accounts as acc
                        INNER JOIN clients_accounts cli_acc 
                            ON cli_acc.account_id = acc.id
                            AND cli_acc.client_code = {code};

                    """)

        cursor_result = cursor.fetchall()

        cursor.close()

        return_object = {}

        return_object['is_live'] = self.get_is_live(first_day_week, last_day_week)
        
        for account in cursor_result:
            week_start_balance = float(account['week_start_balance'])
            equity = float(account['equity'])

            fbalance = self.get_float_balance_by_vars(equity, week_start_balance)
            
            if fbalance > 0:
                apply_deduction_5_percent = float(fbalance * 0.95)
            else:
                apply_deduction_5_percent = float(fbalance)

            account['profit_loss'] = apply_deduction_5_percent

        return_object['products'] = cursor_result

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""

                        SELECT * FROM platform_panel LIMIT 1;

                    """)

        cursor_result_one = cursor.fetchone()

        if cursor_result_one != None and cursor_result_one['is_override'] == True:
            return_object['is_live'] = cursor_result_one['is_live']

            if cursor_result_one['is_live'] == False:
                for product in return_object['products']:
                    product['profit_loss'] = 0.0

        cursor.close()


        bet_performance = self.get_current_day_only_bet_performance()

        product = {}
        product["balance"] = float(bet_performance["balance"])
        product["drawdown"] = 0
        product["equity"] = float(bet_performance["balance"])
        product["id"] = '100100'
        product["product_name"] = "Montagul"
        product["trades"] = 0
        product["profit_loss"] = float(bet_performance["profit_loss"])
        product["week_start_balance"] =  bet_performance["profit_loss"] + bet_performance["balance"]

        return_object['products'].append(product)

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