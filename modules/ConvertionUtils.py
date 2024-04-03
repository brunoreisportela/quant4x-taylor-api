import re
import time
import json
import datetime

from .Structs import *

from decimal import Decimal
from colorama import Fore, Back, Style

class ConvertionUtils:

    def is_valid_json_string(json_string):
        try:
            json.loads(json_string)
            return True
        except ValueError:
            return False

    
    def fetch_to_dict(rows, columns, row_type):
        # Check if rows is None (no result), a single row, or multiple rows
        # Adjust accordingly to always work with a list
        if rows is None:
            return None
        if isinstance(rows, tuple):
            rows = [rows]  # Wrap a single row in a list

        # Extract column names from the cursor description
        column_names = [desc[0] for desc in columns]

        if row_type == RowType.ONE.value:
            return dict(zip(column_names, rows[0]))
        else:
            return [dict(zip(column_names, row)) for row in rows]

    def row_to_dict(row, cursor = None):
        if row is None:
            return None
        
        column_names = [desc[0] for desc in cursor.description]
        
        return dict(zip(column_names, row))
    
    def extract_json(text):
        # Regular expression pattern for JSON
        # This pattern is basic and might need to be adjusted for complex JSON structures
        pattern = r'\{.*?\}|\[.*?\]'

        # Find all matches in the text
        matches = re.findall(pattern, text, re.DOTALL)

        # Attempt to parse each match as JSON
        json_objects = []
        for match in matches:
            try:
                json_objects.append(json.loads(match))
            except json.JSONDecodeError:
                print(f"{Fore.LIGHTRED_EX}Invalid JSON: {match}")
                pass  # If it's not valid JSON, ignore it

        return json_objects

    def json_to_string(json_data):
        """
        Convert a JSON object (dictionary in Python) to a string.
        
        Parameters:
        json_data (dict): The JSON data to convert.
        
        Returns:
        str: The string representation of the JSON data.
        """
        return json.dumps(json_data)

    def string_to_json(string_data):
        """
        Convert a string representation of JSON data back into a dictionary.
        
        Parameters:
        string_data (str): The string representation of JSON data.
        
        Returns:
        dict: The JSON data as a Python dictionary.
        """
        return json.loads(string_data)

    def dict_to_string(dictionary):
        """
        Converts a dictionary into a string representation.
        
        :param dictionary: The dictionary to convert.
        :return: A string representation of the dictionary.
        """
        return json.dumps(dictionary)

    def string_to_dict(string):
        """
        Converts a string representation back into a dictionary.
        
        :param string: The string to convert.
        :return: A dictionary representation of the string.
        """
        return json.loads(string)


    def convert_decimals_to_float(dict_object):
        for key, value in dict_object.items():
            if isinstance(value, Decimal):
                dict_object[key] = float(value)

        return dict_object

    def get_day_epoch_times():
        # Get the current date
        today = datetime.date.today()
        
        # Create datetime objects for the start and end of the day
        start_of_day = datetime.datetime.combine(today, datetime.time.min)
        end_of_day = datetime.datetime.combine(today, datetime.time.max)
        
        # Convert to Unix epoch time
        start_epoch = int(time.mktime(start_of_day.timetuple()))
        end_epoch = int(time.mktime(end_of_day.timetuple()))
        
        return start_epoch, end_epoch

    def compare_distances(distance1, distance2):
        if distance1 > distance2:
            distance = abs(distance1 - distance2)
        else:
            distance = abs(distance2 - distance1)

        return distance

    def convert_to_american_odds(decimal_odds):
        if decimal_odds > 2.0:
            # Underdog
            if decimal_odds != 1.0:
                american_odds = (decimal_odds - 1) * 100
                return int(american_odds)
        elif decimal_odds < 2.0:
            # Favorite
            if decimal_odds != 1.0:
                american_odds = -100 / (decimal_odds - 1)
                return int(american_odds)
        else:
            # Even odds
            return 100

    def convert_floats_in_dict(data_dict):
        for key, value in data_dict.items():
            try:
                # Attempt to convert the value to a float
                float_value = float(value)
                # Replace the original value with the float value
                data_dict[key] = float_value
            except ValueError:
                # If conversion to float fails, just continue
                continue
        return data_dict

    def convert_camel_to_snake(value):
        """
        Recursively converts camelCase keys in dictionaries and lists to snake_case.
        """
        def camel_to_snake(name):
            # Convert camelCase to snake_case
            name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        
        if isinstance(value, dict):
            # Process a dictionary
            return {camel_to_snake(key): ConvertionUtils.convert_camel_to_snake(val) for key, val in value.items()}
        elif isinstance(value, list):
            # Process a list
            return [ConvertionUtils.convert_camel_to_snake(item) for item in value]
        else:
            # Return the value as is if it's not a dictionary or list
            return value
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)