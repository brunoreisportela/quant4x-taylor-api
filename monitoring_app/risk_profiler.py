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

fig, axes = None, None

# Enable interactive mode
plt.ion()

def get_week_boundaries(current_date):
    # Parse the current date
    date_format = "%Y-%m-%d"
    current_date = datetime.strptime(current_date, date_format)

    # Calculate the Sunday and Friday of the week
    start_of_week = current_date - timedelta(days=current_date.weekday() + 2)
    end_of_week = start_of_week + timedelta(days=5)

    # Format the start and end of the week for PostgreSQL timestamp without timezone
    start_of_week_str = start_of_week.strftime("%Y-%m-%d %H:%M:%S")
    end_of_week_str = end_of_week.strftime("%Y-%m-%d %H:%M:%S")

    # Prepare the JSON output with separated day, month, and year
    result = {
        "sunday": {
            "day": start_of_week.day,
            "month": start_of_week.month,
            "year": start_of_week.year,
            "timestamp": start_of_week_str
        },
        "friday": {
            "day": end_of_week.day,
            "month": end_of_week.month,
            "year": end_of_week.year,
            "timestamp": end_of_week_str 
        }
    }

    return result

def plot_performance():
    global fig, axes

    # Check if fig and axes are already initialized
    if fig is None or axes is None:
        # Create figure and axes if they don't exist
        fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(21, 6), sharex='col')
    else:
        # Clear existing axes for update
        for ax in axes:
            ax.clear()

    try:
        df = get_performance_data()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    try: 
        # Convert 'created_at' to datetime
        df['created_at'] = pd.to_datetime(df['created_at'])

        # Convert 'profit_loss' and 'drawdown' to numeric, handling NaNs
        df['profit_loss'] = pd.to_numeric(df['profit_loss'], errors='coerce').fillna(0)
        df['drawdown'] = pd.to_numeric(df['drawdown'], errors='coerce').fillna(0)

        # Sort by 'created_at' for chronological plotting
        df.sort_values('created_at', inplace=True)

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
        # plt.show()

        plt.draw()
        plt.pause(1800)  # Pause briefly to allow plot to be drawn

    except Exception as e:
        print(f"Error during plotting: {e}")

def get_performance_data():
    # Initialize connection and cursor within the function
    global conn,cursor  # Ensure conn is accessible

    current_date = datetime.now() # Example current date and time
    next_date = current_date + timedelta(days=1)

    day = next_date.day
    month = next_date.month
    year = next_date.year
    hour = next_date.hour
    minute = next_date.minute

    week_boundaries = get_week_boundaries(f"{year}-{month}-{day}")

    sql = f"""
                SELECT * FROM platform_performance WHERE created_at >= '{week_boundaries['sunday']['timestamp']}'
          """
    
    cursor.execute(sql)

    data = cursor.fetchall()

    # cursor.close()

    # Replace 'column_names_here' with your actual column names
    columns = ['ID', 'product_name', 'updated_at', 'created_at', 'profit_loss', 'equity', 'year', 'month', 'day', 'drawdown']
   
    df = pd.DataFrame(data, columns=columns)
    
    return df

if __name__ == "__main__":

    try:
        conn = psycopg2.connect(database="defaultdb",
                                host="quant4x-admin-database-do-user-3044858-0.b.db.ondigitalocean.com",
                                user="doadmin",
                                password="AVNS_KmHOAPDB_osaTG-XvN9",
                                port="25060")
        conn.autocommit = True

        if conn is None:
            print("Failed to connect to the database.")
        else:
            print("Database connection established successfully.")
        
        cursor = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        while True:
            try:
                plot_performance()  # Ensure this function uses a freshly created cursor each time
                print("Plot updated at:", datetime.now())
                # time.sleep(1800)  # 30 minutes
                # time.sleep(10)  # 30 minutes
            except Exception as e:
                print(f"Error updating plot - {e}")
            except KeyboardInterrupt:
                print("Program terminated by user.")
                break
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")

    