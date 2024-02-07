import argparse
import json
import datetime
import psycopg2
import psycopg2.extras
import pandas as pd
import matplotlib.pyplot as plt
from math import pi

import time
from datetime import datetime, timedelta


conn = None
cursor = None

def plot_performance():
    # Fetch the data
    df = get_performance_data()

    # RADAR
    radar_df = df.groupby('product_name').agg({'profit_loss': 'mean', 'drawdown': 'mean'}).reset_index()
    # Number of variable
    categories = list(radar_df)[1:]  # ['profit_loss', 'drawdown']
    N = len(categories)
    # What will be the angle of each axis in the plot? (we divide the plot / number of variable)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]  # Complete the loop
    # END RADAR
    
    # Convert 'created_at' to datetime
    df['created_at'] = pd.to_datetime(df['created_at'])

    # Convert 'profit_loss' and 'drawdown' to numeric, handling NaNs
    df['profit_loss'] = pd.to_numeric(df['profit_loss'], errors='coerce').fillna(0)
    df['drawdown'] = pd.to_numeric(df['drawdown'], errors='coerce').fillna(0)

    # Sort by 'created_at' for chronological plotting
    df.sort_values('created_at', inplace=True)
    
    # Adjust the subplot grid to 1 row, 3 columns
    fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(21, 6), sharex='col')

    # Plot Profit/Loss and Drawdown over time for each product
    unique_products = df['product_name'].unique()
    for product in unique_products:
        product_df = df[df['product_name'] == product]
        axes[0].plot(product_df['created_at'], product_df['profit_loss'], label=product)
        axes[1].plot(product_df['created_at'], product_df['drawdown'], label=product)

    # Set titles and labels for the first two plots
    axes[0].set_title('Profit/Loss by Product Name over Time')
    axes[0].set_xlabel('Date')
    axes[0].set_ylabel('Profit/Loss')
    axes[0].legend(loc="best")
    
    axes[1].set_title('Drawdown by Product Name over Time')
    axes[1].set_xlabel('Date')
    axes[1].set_ylabel('Drawdown')
    axes[1].legend(loc="best")
    
    # Plot histogram of drawdowns grouped by product name in the third subplot
    for product in unique_products:
        product_df = df[df['product_name'] == product]
        axes[2].hist(product_df['drawdown'], label=product, alpha=0.5, bins=20)

    axes[2].set_title('Histogram of Drawdowns by Product Name')
    axes[2].set_xlabel('Drawdown')
    axes[2].set_ylabel('Frequency')
    axes[2].legend(loc="best")
    
    plt.tight_layout()
    plt.show()

def get_performance_data():

    sql = f"""
                SELECT * FROM platform_performance;  
          """
    
    cursor.execute(sql)

    data = cursor.fetchall()

    cursor.close()

    # Replace 'column_names_here' with your actual column names
    columns = ['ID', 'product_name', 'updated_at', 'created_at', 'profit_loss', 'equity', 'year', 'month', 'day', 'drawdown']
    df = pd.DataFrame(data, columns=columns)
    
    return df

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
        plot_performance()
    except Exception as e:
        print(f"APP FAILED - {e}")
        # create_app()
    except KeyboardInterrupt:
        print("Program finished by user.")
    pass

    if conn != None:
        conn.close()
        

    