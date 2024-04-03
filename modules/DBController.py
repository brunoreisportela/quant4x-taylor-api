import psycopg2
import datetime
import psycopg2.extras

from psycopg2 import sql
from .Structs import *
from .ConvertionUtils import *

class DBController:

    db = None
    connection_string = 'postgresql://doadmin:AVNS_KmHOAPDB_osaTG-XvN9@botbetiq-pg-prod-do-user-3044858-0.c.db.ondigitalocean.com:25060/hive?sslmode=require'

    def __init__(self):
        self.db = psycopg2.connect(self.connection_string)
        self.create_table()

    def execute_query(self, query, params=(), fetchone=False, fetchall=False, commit=False):
        with self.db as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if commit:
                    conn.commit()
                if fetchone:
                    return cursor.fetchone(), cursor.description
                if fetchall:
                    return cursor.fetchall(), cursor.description
                return cursor.rowcount

    def create_table(self):
        create_table_query = sql.SQL(f'''CREATE TABLE IF NOT EXISTS tasks (
                              id TEXT PRIMARY KEY, 
                              prompt TEXT, 
                              webhook TEXT, 
                              answer TEXT, 
                              processor TEXT, 
                              status TEXT default '{StatusType.PENDING.value}',
                              collected_status TEXT default '{StatusType.PENDING.value}',
                              created_at TIMESTAMP, 
                              updated_at TIMESTAMP)''')
        self.execute_query(create_table_query)

    def insert_task(self, task):
        now_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task["created_at"] = now_date
        task["updated_at"] = now_date

        return self.execute_query("INSERT INTO tasks (id, prompt, webhook, answer, processor, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                   (task["id"], task["prompt"], task["webhook"], task["answer"], task["processor"], task["created_at"], task["updated_at"]), 
                                   commit=True)
    
    def update_task(self, task):
        now_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task["updated_at"] = now_date

        return self.execute_query("UPDATE tasks SET answer=%s, status=%s, updated_at=%s, collected_status=%s WHERE id=%s", 
                                   (task["answer"], task["status"], task["updated_at"], task["collected_status"], task["id"]), 
                                   commit=True)

    def get_task(self, task_id):
        row, columns = self.execute_query("SELECT * FROM tasks WHERE id=%s", (task_id,), fetchone=True)
        row_data = ConvertionUtils.fetch_to_dict(row, columns, RowType.ONE.value)
        return row_data if row_data else {}

    def get_next_pending_task(self):
        row,columns = self.execute_query("SELECT * FROM tasks WHERE status = %s ORDER BY created_at ASC LIMIT 1",(StatusType.PENDING.value,), fetchone=True)

        row_data = ConvertionUtils.fetch_to_dict(row, columns, RowType.ONE.value)
        return row_data if row_data else {}

    def get_next_waiting_task(self):
        row,columns = self.execute_query("SELECT * FROM tasks WHERE collected_status = %s ORDER BY created_at ASC LIMIT 1",(StatusType.WAITING.value,), fetchone=True)

        row_data = ConvertionUtils.fetch_to_dict(row, columns, RowType.ONE.value)
        return row_data if row_data else {}

    def get_pending_tasks_collection(self, processor):
        rows, columns = self.execute_query("SELECT * FROM tasks WHERE processor=%s AND status=%s ORDER BY created_at DESC",(processor, StatusType.PENDING.value,), fetchall=True)
        rows_data = ConvertionUtils.fetch_to_dict(rows, columns, RowType.ALL)
        return rows_data if rows_data else []
    
    def get_waiting_tasks_collection(self, processor):
        rows, columns = self.execute_query("SELECT * FROM tasks WHERE processor=%s AND collected_status=%s ORDER BY created_at DESC",(processor, StatusType.WAITING.value,), fetchall=True)
        rows_data = ConvertionUtils.fetch_to_dict(rows, columns, RowType.ALL)
        return rows_data if rows_data else []
