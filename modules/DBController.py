import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta

class DBController:

    conn = None
    cursor = None

    def get_client_by_code(self, code):
        self.cursor.execute(f"SELECT * FROM clients AS cli WHERE cli.code = {code}")

        cursor_result = self.cursor.fetchone()

        if cursor_result == None:
            return None
        else:
            return cursor_result
        
    def get_client_accounts_by_code(self, code):
        self.cursor.execute(f"SELECT * FROM clients AS cli INNER JOIN accounts AS acc ON acc.client_code = cli.code WHERE cli.code = {code}")

        cursor_result = self.cursor.fetchone()

        if cursor_result == None:
            return None
        else:
            return cursor_result
        
    def set_user_code(self, email, code):

        sql = f"UPDATE users SET code = '{code}' WHERE email = '{email}'"
        
        self.cursor.execute(sql)

        self.conn.commit()
        
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
    
    def get_user_code(self, email, code):

        self.cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")

        cursor_result = self.cursor.fetchone()

        if cursor_result == None:
            return None
        else:
            return cursor_result
        
    def get_profit_percentage_by_code(self, code):
        
        profit = 0.0
        balance = 0.0

        for result in self.get_positions_by_code(code):
            profit += result["profit_loss"]
            balance += result["balance"]

        total_to_take = abs(balance)+abs(profit)
        total_profit_percent = round((profit/(abs(balance)+abs(profit))) * 100, 2)

        return ""

        # abs(total_balance)+abs(total_profit_loss)
        # round((client_dict["total_profit_loss"]/client_dict["total_to_take"]) * 100, 2)
        
    def get_positions_by_code(self, code):        

        dt = datetime.today()
        first_day_week = self.get_first_day_week(dt)
        last_day_week = self.get_last_day_week(dt)

        self.cursor.execute(f"""

                        SELECT * FROM accounts as acc
                        INNER JOIN clients_accounts cli_acc 
                            ON cli_acc.account_id = acc.id
                            AND cli_acc.client_code = {code};

                    """)

        cursor_result = self.cursor.fetchall()

        return_object = {}

        return_object['is_live'] = self.get_is_live(first_day_week, last_day_week)

        # total_week_profit = 0
        # total_week_balance = 0

        # products = []

        # for result in cursor_result:

            # product_dict = {}

            # percent = 0
            # profit_loss = result[u'profit_loss']
            # balance = result[u'balance']

            # if profit_loss != 0 and balance != 0:
            #     percent += ( profit_loss / balance ) * 100

            # product_dict[u'name'] = result[u'product_name']
            # product_dict[u'profit_loss'] = profit_loss
            # product_dict[u'drawdown'] = result[u'drawdown']
            # product_dict[u'balance'] = result[u'balance']
            # product_dict[u'equity'] = result[u'equity']
            # product_dict[u'percent'] = percent

            # products.append(result)

            # total_week_profit += profit_loss
            # total_week_balance += balance

        return_object['products'] = cursor_result

        # avg_profit_percent = (total_week_profit / total_week_balance) * 100
        # avg_profit = total_week_profit

        # return_object['avg_profit_percent'] = avg_profit_percent
        # return_object['week_profit'] = avg_profit

        # return_object['balance'] = total_week_balance
        # return_object['profit_loss'] = total_week_profit

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

    def get_positions_pl(self, code, account_id, fmt_first_day):        

        dt = datetime.today()

        first_day_week = self.get_first_day_week(dt)
        
        fmt_first_day = first_day_week.strftime("%Y-%m-%d")

        self.cursor.execute(f"""

                                SELECT account_id, sum(PL) as pl FROM 
                                (

                                    SELECT pos.account_id, (sum(pos.commission)+sum(profit)+sum(swap)) as PL from positions pos 
                                        INNER JOIN clients_accounts cli_acc ON cli_acc.account_id = pos.account_id
                                        INNER JOIN accounts acc on acc.id = cli_acc.account_id
                                        WHERE cli_acc.client_code = {code} 
                                            AND pos.close_time >= TO_TIMESTAMP('{fmt_first_day}','YYYY-MM-DD')
                                            AND pos.type != 6
                                            AND pos.account_id = '{account_id}'
                                        GROUP BY pos.ticket, pos.account_id

                                ) 
                                as positions GROUP BY account_id;

                            """)

        cursor_result = self.cursor.fetchall()

        if cursor_result == None:
            return None
        else:
            return cursor_result

    def __init__(self, *args, **kwargs):

        self.conn = psycopg2.connect(database="defaultdb",
                        host="quant4x-admin-database-do-user-3044858-0.b.db.ondigitalocean.com",
                        user="doadmin",
                        password="AVNS_KmHOAPDB_osaTG-XvN9",
                        port="25060")
        
        self.cursor = self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        super().__init__(*args, **kwargs)