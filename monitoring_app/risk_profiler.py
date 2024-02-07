import argparse
import json
import datetime
import psycopg2
import psycopg2.extras

import time
from datetime import datetime, timedelta


conn = None
cursor = None

def get_performance_data():

    sql = f"""
                SELECT * FROM platform_performance;  
          """
    
    cursor.execute(sql)

    cursor_result = cursor.fetchall()

    cursor.close()

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
        get_performance_data()
    except Exception as e:
        print(f"APP FAILED - {e}")
        # create_app()
    except KeyboardInterrupt:
        print("Program finished by user.")
    pass

    if conn != None:
        conn.close()
        

    