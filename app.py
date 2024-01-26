import os
import sys
import json

from flask import Flask,request,render_template, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from modules import DBController

app = Flask(__name__)
CORS(app)

dbController = DBController()

valid_tokens = {"c5c917655b6d0ax008ssd2d92026f772"}

@app.route("/")
def get_service():
    return get_echo()

@app.route("/echo")
def get_echo():
    return "Echo"

@app.route("/clients", methods=['GET'])
def get_clients():
    return json.dumps(dbController.get_clients())

@app.route("/clients/report/scope", methods=['GET'])
def get_clients_report_scope():
    start_date = dbController.stringToDate(request.args["start_date"])
    end_date = dbController.stringToDate(request.args["end_date"])

    return json.dumps(dbController.get_clients(start_date, end_date))

@app.route("/message/telegram", methods=['POST'])
def send_message_telegram():
    token = request.headers.get('Authorization') 

    if token not in valid_tokens:
        return {"error": "Invalid token"}, 401
    
    message = request.form["message"]
    dbController.send_telegram_message(message)

    return "Ok"

@app.route("/products/performance", methods=['GET'])
def get_products_performance():
    return get_platform_performance()

@app.route("/bot/message/from/group", methods=['GET'])
def get_bot_message_from_group():
    try:
        return dbController.get_bot_message_from_group()
    except Exception as e:
        return json.dumps({"error": str(e)})

def get_platform_performance():
    return dbController.get_platform_performance(1)

@app.route("/update/accounts/kpi", methods=['GET'])
def update_accounts_kpi():
    return dbController.update_accounts_kpi()

@app.route("/accounts/week_start_balance", methods=['GET'])
def get_week_start_balance_by_account_id():
    account_id = request.args["account_id"]
    return json.dumps(dbController.get_week_start_balance_by_account_id(account_id))

@app.route("/accounts/setup", methods=['GET'])
def get_json_setup():
    account_id = request.args["account_id"]
    return json.dumps(dbController.get_json_setup(account_id))

@app.route("/accounts/is_live_active", methods=['GET'])
def get_is_live_active_by_account_id():
    account_id = request.args["account_id"]
    return json.dumps(dbController.get_is_live_active_by_account_id(account_id))

@app.route("/accounts/invest_code", methods=['GET'])
def get_invest_code_by_account_id():
    account_id = request.args["account_id"]
    return json.dumps(dbController.get_invest_code_by_account_id(account_id))

@app.route("/accounts/week_target", methods=['GET'])
def get_week_target_by_account_id():
    account_id = request.args["account_id"]
    return json.dumps(dbController.get_week_target_by_account_id(account_id))

@app.route("/accounts/week_loss_target", methods=['GET'])
def get_week_loss_target_by_account_id():
    account_id = request.args["account_id"]
    return json.dumps(dbController.get_week_loss_target_by_account_id(account_id))

@app.route("/kpi/cluster", methods=['GET'])
def aggregate_float_dd_KPI_per_cluster():
    return json.dumps(dbController.aggregate_float_dd_KPI_per_cluster())

@app.route("/products/performance/code", methods=['GET'])
def get_products_performance_code():
    code = request.args["code"]
    return dbController.get_performance_by_code(code)

@app.route("/percent/performance/code", methods=['GET'])
def get_percent_performance_code():
    code = request.args["code"]
    cluster_id = 1

    if "cluster_id" in request.args:
        cluster_id = request.args["cluster_id"]

    return json.dumps(dbController.get_profit_percentage_by_code(code, cluster_id))

@app.route("/whatsapp/send_message", methods=['POST'])
def post_whatsapp_send_message():
    payload = request.form["payload"]
    return dbController.send_whatsapp_message(payload)

@app.route("/taylor/says", methods=['POST'])
def taylor_says():
    message = request.form["message"]
    return dbController.taylor_says_telegram(message)

@app.route("/add/performance", methods=['POST'])
def add_performance():
    token = request.headers.get('Authorization') 

    if token not in valid_tokens:
        return {"error": "Invalid token"}, 401
    
    payload = json.loads(request.data)    
    
    return dbController.add_performance(payload)

@app.route("/day/performance", methods=['GET'])
def day_performance():
    token = request.headers.get('Authorization') 

    if token not in valid_tokens:
        return {"error": "Invalid token"}, 401
    
    current_day_performance = dbController.get_current_day_performance()
    
    profit_loss = 0
    cycle = 0

    if "profit_loss" in current_day_performance:
        profit_loss = float(current_day_performance["profit_loss"])

    if "cycle" in current_day_performance:
        cycle = int(current_day_performance["cycle"])

    message = ""
    
    if profit_loss > 0:
        message = f"📈Accumulated result - Cycle {cycle}: +${profit_loss:.2f}"
    elif profit_loss < 0:
        message = f"📉Accumulated result - Cycle {cycle}: -${profit_loss:.2f}"

    if message != "":
        dbController.send_telegram_message(message)

    return current_day_performance

@app.route("/day/performance/push", methods=['GET'])
def day_performance_push():
    current_day_performance = dbController.get_current_day_performance()
    
    if "profit_loss" in current_day_performance:
        current_day_performance["profit_loss"] = float(current_day_performance["profit_loss"])
    else:
        current_day_performance["profit_loss"] = 0.0

    if "cycle" in current_day_performance:
        current_day_performance["cycle"] = int(current_day_performance["cycle"])
    else:
        current_day_performance["cycle"] = 0

    dbController.send_push_broadcast(current_day_performance)

    return current_day_performance

@app.route("/day/performance/whatsapp", methods=['GET'])
def day_performance_whatsapp():
    token = request.headers.get('Authorization') 

    if token not in valid_tokens:
        return {"error": "Invalid token"}, 401
    
    current_day_performance = dbController.get_current_day_performance()
    
    if "profit_loss" in current_day_performance:
        current_day_performance["profit_loss"] = float(current_day_performance["profit_loss"])
    else:
        current_day_performance["profit_loss"] = 0.0

    if "cycle" in current_day_performance:
        current_day_performance["cycle"] = int(current_day_performance["cycle"])
    else:
        current_day_performance["cycle"] = 0

    dbController.send_whatsapp_broadcast(current_day_performance)

    return current_day_performance

@app.route("/taylor/answer", methods=['POST'])
def taylor_get_answer():
    message = request.form["message"]
    return dbController.taylor_get_answer(message)

@app.route("/client/code", methods=['GET'])
def get_client_code():
    code = request.args["code"]

    dt = datetime.today()
    start_date_fmt = dbController.dateToString(dbController.get_first_day_week(dt))
    end_date_fmt = dbController.dateToString(dbController.get_last_day_week(dt))

    return json.dumps(dbController.get_client_by_code(code, start_date_fmt, end_date_fmt))

@app.route("/webhook", methods=["POST"])
def webhook():
    json_data = request.get_json()

    print(json_data,  file=sys.stdout, flush=True)

    wttype = json_data["type"]

    if wttype == "message":

        message = json_data["message"]
        conversation = json_data["user"]["phone"]
        _type = message["type"]
        
        if message["fromMe"]:
            return
        
        if _type == "text":
            
            text = message["text"]
            text = text.lower()

            response_from_ai = str(dbController.taylor_get_answer(text))

            body = {"type": "text","message": response_from_ai}
            body.update({"to_number": conversation})
            
            dbController.send_whatsapp_message(body)
    else:
        print("Unknow Type:", wttype,  file=sys.stdout, flush=True)
        
    return jsonify({"success": True}), 200