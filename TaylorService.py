import time
import uuid
import requests
import colorama

from tabulate import tabulate
from datetime import datetime
from colorama import Fore, Back, Style

from modules.DBController import DBController
from modules.SimilarityUtils import *
from modules.Structs import *
from modules.ConvertionUtils import *
from modules.ScreenUtils import *

from modules_taylor import DBController as DBControllerModules

colorama.init(autoreset=True)

class TaylorService:

    db_controller = DBController()
    db_controller_modules = DBControllerModules()

    def schedule_task(self, symbol_name):
        task_id = str(uuid.uuid4())
        print(f"Queue added to the pipeline: {task_id}")

        task = Task
        task["id"] = task_id
        task["processor"] = ProcessorType.PROMPT_INVESTMENT_CREW.value
        task["status"] = StatusType.PENDING.value
        task["prompt"] = symbol_name
        task["webhook"] = ""

        return self.db_controller.insert_task(task)

    def get_task_id(self, event):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        payload = {
            "pair": event["name"]
        }
            
        response = requests.post(f"{self.api_base_URL}/prompt/bet/tennis/crew", headers=headers, data=payload)
        if response.status_code == 200 or response.status_code == 201:
            if "task_id" in response.json():
                task_id = response.json()["task_id"]
                print(f"{Fore.LIGHTGREEN_EX}Task ID: {Fore.LIGHTYELLOW_EX}{task_id}")
                return task_id
        else:
            print(f"{Fore.LIGHTRED_EX}Error {response.status_code}: {response.text}")

    def load_waiting_tasks(self):
        
        waiting_tasks = self.db_controller.get_waiting_tasks_collection(ProcessorType.PROMPT_INVESTMENT_CREW.value)

        if len(waiting_tasks) > 0:
            for task in waiting_tasks:
                try:
                    answer_json = ConvertionUtils.string_to_json( ConvertionUtils.string_to_json( task["answer"] ))

                    if "pair" in answer_json and "sentiment" in answer_json:
                        pair = str(answer_json["pair"]).replace("/","")
                        pair = pair.upper()

                        sentiment = str(answer_json["sentiment"]).lower()

                        if sentiment != "bullish" and sentiment != "bearish":
                            sentiment = "mixed"

                        self.db_controller_modules.save_sentiment_pair(pair, sentiment)

                        task["collected_status"] = StatusType.COLLECTED.value
                        self.db_controller.update_task(task)

                except Exception as e:
                    task["collected_status"] = StatusType.COLLECTED.value
                    self.db_controller.update_task(task)
                    print(f"{Fore.LIGHTRED_EX}Error: {e}")
        
        return waiting_tasks
    
    def sync_symbols_to_predict(self):
        list_to_predict = ["GBPUSD", "EURUSD", "USDJPY", "USDCAD", "GOLD", "SP500"]

        for symbol in list_to_predict:
            
            cursor_count = self.schedule_task(symbol)

            if cursor_count > 0:
                print(f"{Fore.LIGHTGREEN_EX}Symbol {symbol} inserted")
            else:
                print(f"{Fore.LIGHTYELLOW_EX}Warning: Symbol {symbol} not inserted")

        self.load_waiting_tasks()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.sync_symbols_to_predict()
        time.sleep(1)
        self.load_waiting_tasks()
        time.sleep(1)

if __name__ == "__main__":
    print(Fore.LIGHTYELLOW_EX+"Application Opened")

    TaylorService()
    
    print(Fore.LIGHTYELLOW_EX+"Trigering Interval Before Close Application - 300 seconds")
    time.sleep(3600)