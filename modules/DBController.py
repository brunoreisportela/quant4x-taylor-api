import psycopg2
import psycopg2.extras

class DBController:

    conn = None
    cursor = None

    def set_user_code(self, email, code):

        sql = f"UPDATE users SET code = '{code}' WHERE email = '{email}'"
        
        self.cursor.execute(sql)

        self.conn.commit()
        
        return ""
    
    def get_user_code(self, email, code):

        self.cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")

        cursor_result = self.cursor.fetchone()

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