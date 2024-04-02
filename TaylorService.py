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

    api_base_URL = "https://taylor.ngrok.app"
    cloudbet_URL = "https://sports-api.cloudbet.com/pub/v2"

    cloudbet_key = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkhKcDkyNnF3ZXBjNnF3LU9rMk4zV05pXzBrRFd6cEdwTzAxNlRJUjdRWDAiLCJ0eXAiOiJKV1QifQ.eyJhY2Nlc3NfdGllciI6InRyYWRpbmciLCJleHAiOjIwMTc2Nzc4NDYsImlhdCI6MTcwMjMxNzg0NiwianRpIjoiYTU5NGVmMzQtNWQ0My00OWZkLWFlY2UtNjVkOWM3NzlkOGRmIiwic3ViIjoiN2QxMDBjY2UtNWU0Ni00ZjI0LWJiNTEtYWVkNWQ1ODQ2YjAwIiwidGVuYW50IjoiY2xvdWRiZXQiLCJ1dWlkIjoiN2QxMDBjY2UtNWU0Ni00ZjI0LWJiNTEtYWVkNWQ1ODQ2YjAwIn0.aON3xNrNxUix8F7wFhg85ZtnaU0PUsW4rk3LKhCHJEK4CD6i9FXomt80QsRAF2TJAmRnEdcK0drYVVv61XqwSjwcYM3AvuUwfmakysI8VBH5FEiLWLXQLxo6Y1Jns9XrnGKECNIaqG5ejQm_f1KLUDwVTxMSyk84aFgNPLQob5Q-obUyaWB9ZAq4IT-N9HiZzvyMulYRG7t2YIaGacZOvkukvaZGKH8pMMY8IzxfK1TIwStSs2NkS7WmEuHe-x9_YUJHMOPpZ7bflIYW35iXt00e6TuB7UBEs6oad2JgRx8urVMqANw1_zlz8zJmNIZUWr7Q7UARYVG35ECAeSSbMQ"

    def schedule_task(self, event_name):
        task_id = str(uuid.uuid4())
        print(f"Queue added to the pipeline: {task_id}")

        task = Task
        task["id"] = task_id
        task["processor"] = ProcessorType.PROMPT_BET_TENNIS_CREW.value
        task["status"] = StatusType.PENDING.value
        task["prompt"] = event_name
        task["webhook"] = ""

        self.db_controller_modules.insert_task(task)

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
        
        waiting_tasks = self.db_controller_modules.get_waiting_tasks_collection(ProcessorType.PROMPT_BET_TENNIS_CREW.value)

        if len(waiting_tasks) > 0:
            for task in waiting_tasks:
                # self.db_controller.update_event_by_name(task['prompt'], task)

                event = self.db_controller.get_event_by_name(task['prompt'])

                if event:
                    if "id" in task and "answer" in task:
                        has_valid_json_string = ConvertionUtils.is_valid_json_string(task["answer"])
                        
                        if has_valid_json_string:
                            task_answer_to_dict = ConvertionUtils.string_to_dict(task["answer"])

                            if "probable_winner" in task_answer_to_dict and "reason_why_the_probable_outcome" in task_answer_to_dict:

                                task_id = task["id"]
                                probable_winner = task_answer_to_dict["probable_winner"]
                                reason_why_the_probable_outcome = task_answer_to_dict["reason_why_the_probable_outcome"]

                                if probable_winner and reason_why_the_probable_outcome:

                                    home_score = 0
                                    away_score = 0

                                    home_score = SimilarityUtils().jaccard_similarity(probable_winner, event["player_home_name"])
                                    away_score = SimilarityUtils().jaccard_similarity(probable_winner, event["player_away_name"])

                                    probable_winner = "undefined"

                                    if home_score > away_score and home_score > 0.5:
                                        probable_winner = "home"
                                    if away_score > home_score and away_score > 0.5:
                                        probable_winner = "away"
                                        
                                    print(f"{Fore.LIGHTYELLOW_EX}Task ID: {Fore.LIGHTGREEN_EX}{task['id']} - {task['prompt']} - {probable_winner}")
                                    self.db_controller.update_event(event, task_id, probable_winner, reason_why_the_probable_outcome)


                                    task["collected_status"] = StatusType.COLLECTED.value
                                    self.db_controller_modules.update_task(task)

                                else:
                                    task["collected_status"] = StatusType.COLLECTED.value
                                    self.db_controller_modules.update_task(task)
                                    self.db_controller.update_event(event, task_id, "undefined", "INVALID_JSON")
                            else:
                                task["collected_status"] = StatusType.COLLECTED.value
                                self.db_controller_modules.update_task(task)
                                self.db_controller.update_event(event, task_id, "undefined", "INVALID_JSON")
                        else:
                            task["collected_status"] = StatusType.COLLECTED.value
                            self.db_controller_modules.update_task(task)
                            self.db_controller.update_event(event, task_id, "undefined", "INVALID_JSON")
                    else:
                        task["collected_status"] = StatusType.COLLECTED.value
                        self.db_controller_modules.update_task(task)
                        self.db_controller.update_event(event, "no_relation", "undefined", "INVALID_JSON")
        
        return waiting_tasks

    def normalize_event(self, event):
        sport_name = "tennis"

        if "players" in event and "markets" in event["players"][0] and "markets" in event["players"][1]:
            for player in event["players"]:
                for market in player["markets"]:
                    if market["type"] == f"{sport_name}.winner":
                        player["american_odd"] = ConvertionUtils.convert_to_american_odds(player["price"])
                        player["market_type"] = market["type"]
                        player["probability"] = market["probability"]
                        player["max_stake"] = market["maxStake"]

                    if market["type"] == f"{sport_name}.winner_of_set":
                        event["current_set"] = market["params"]

            event["american_odd_distance"] = ConvertionUtils.compare_distances(event["players"][0]["american_odd"], event["players"][1]["american_odd"])

            event["max_stake"] = event["players"][0]["max_stake"] if event["players"][0]["max_stake"] > event["players"][1]["max_stake"] else event["players"][1]["max_stake"]

            event["home_american_odd"] = event["players"][0]["american_odd"]
            event["away_american_odd"] = event["players"][1]["american_odd"]
        
        event = ConvertionUtils.convert_camel_to_snake(event)
        return event
        
    def sync_events_to_predict(self):
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.cloudbet_key,
        }
        
        sport_name = "tennis"

        start_epoch, end_epoch = ConvertionUtils.get_day_epoch_times()

        response = requests.get(f"{self.cloudbet_URL}/odds/events?sport={sport_name}&from={start_epoch}&to={end_epoch}&live=false&limit=10000", headers=headers, timeout=120)
        
        print(f"{Fore.GREEN}Event Request Status: {response.status_code} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        events = []

        if response.status_code == 200:
            
            if "events" in response.json() == False:
                return events
            
            json_competitions = response.json()["competitions"]

            for competition in json_competitions:
                json_events = competition["events"]

                print(f"{Fore.GREEN}Events: {Fore.LIGHTYELLOW_EX}{len(json_events)} - {Fore.GREEN}{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                for event in json_events:
                    event = self.normalize_event(event)

                    event_to_predict = {}
                    event_to_predict["id"] = event["id"]
                    event_to_predict["name"] = event["name"]
                    event_to_predict["player_home_name"] = event["home"]["name"]
                    event_to_predict["player_away_name"] = event["away"]["name"]

                    cursor_count = self.db_controller.insert_event(event_to_predict)

                    if cursor_count > 0:
                        self.schedule_task(event_to_predict["name"])
                    else:
                        print(f"{Fore.LIGHTYELLOW_EX}Warning: Event not inserted")

        else:
            print(f"{Fore.LIGHTRED_EX}Error {response.status_code}: {response.text}")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.sync_events_to_predict()
        time.sleep(1)
        self.load_waiting_tasks()
        time.sleep(1)        
        # self.load_pending_events(tasks)

if __name__ == "__main__":
    print(Fore.LIGHTYELLOW_EX+"Application Opened")

    TaylorService()
    
    print(Fore.LIGHTYELLOW_EX+"Trigering Interval Before Close Application - 300 seconds")
    time.sleep(300)