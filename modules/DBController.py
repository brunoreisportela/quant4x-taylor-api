import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta

class DBController:

    conn = None

    def get_client_by_code(self, code):
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"SELECT * FROM clients AS cli WHERE cli.code = {code}")

        cursor_result = cursor.fetchone()

        cursor.close()

        client_dict = {}

        client_dict["code"] = cursor_result["code"]
        client_dict["name"] = cursor_result["name"]
        client_dict["week_balance"] = float(cursor_result["week_balance"])
        client_dict["week_profit_loss"] = float(cursor_result["week_profit_loss"])
        client_dict["week_profit_percent"] = float(cursor_result["week_profit_percent"])

        return client_dict
        
    def get_client_accounts_by_code(self, code):

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"SELECT * FROM clients AS cli INNER JOIN accounts AS acc ON acc.client_code = cli.code WHERE cli.code = {code}")

        cursor_result = cursor.fetchone()

        cursor.close()

        if cursor_result == None:
            return None
        else:
            return cursor_result
        
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
    
    def get_clients(self):

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"SELECT * FROM clients")

        cursor_result = cursor.fetchall()

        cursor.close()

        clients = []

        for client in cursor_result:
            client_dict = {}

            client_dict["code"] = client["code"]
            client_dict["name"] = client["name"]
            client_dict["week_balance"] = float(client["week_balance"])
            client_dict["week_profit_loss"] = float(client["week_profit_loss"])
            client_dict["week_profit_percent"] = float(client["week_profit_percent"])

            clients.append(client_dict)

        return clients
        
    def update_accounts_kpi(self):

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT * FROM clients;
                    """)
        
        clients_result = cursor.fetchall()

        cursor.close()

        clients_codes = []

        for client in clients_result:
            clients_codes.append(client["code"])

        for code in clients_codes:

            cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

            cursor.execute(f"""
                            SELECT * FROM accounts as acc
                            INNER JOIN clients_accounts cli_acc 
                                ON cli_acc.account_id = acc.id
                                AND cli_acc.client_code = {code};
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
                    WHERE code = '{code}'"""
            
            cursor.execute(sql)

            self.conn.commit()

            cursor.close()

        return ""
        
    def get_profit_percentage_by_code(self, code):
        
        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""
                        SELECT * FROM accounts as acc
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

        total_profit_percent = round((profit_loss/(abs(balance)+abs(profit_loss))) * 100, 2)

        return total_profit_percent
    
    def get_performance_by_code(self, code):        

        cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        cursor.execute(f"""

                        SELECT * FROM accounts as acc
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

                        SELECT * FROM accounts as acc
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

        super().__init__(*args, **kwargs)