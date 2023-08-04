import os
import sys
# import json as simplejson
import json

# print(f"SYS PATH: {sys.path}")
# sudo lsof -i -P -n | grep LISTEN

from flask import Flask,request,render_template, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

# from modules import Talk
# from modules import Whatsapp
# from modules import Sentiment
from modules import MayTapi
# from modules import NewsReader
from modules import DBController

app = Flask(__name__)
CORS(app)

# whatsapp = Whatsapp()
# symbol_sentiment = Sentiment()
maytapi = MayTapi()
dbController = DBController()

# talk = Talk()
# newsReader = NewsReader()

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

@app.route("/products/performance/code", methods=['GET'])
def get_products_performance_code():
    code = request.args["code"]
    return dbController.get_performance_by_code(code)

@app.route("/percent/performance/code", methods=['GET'])
def get_percent_performance_code():
    code = request.args["code"]
    return json.dumps(dbController.get_profit_percentage_by_code(code))

@app.route("/whatsapp/send_message", methods=['POST'])
def post_whatsapp_send_message():
    payload = request.form["payload"]
    return maytapi.sendMessage(payload)


@app.route("/taylor/says", methods=['POST'])
def taylor_says():
    message = request.form["message"]
    return dbController.taylor_says_telegram(message)

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

    wttype = json_data["type"]

    if wttype == "message":

        message = json_data["message"]
        conversation = json_data["conversation"]
        _type = message["type"]
        
        if message["fromMe"]:
            return
        
        if _type == "text":
            # Handle Messages
            text = message["text"]
            text = text.lower()

            body = {"type": "text","message": dbController.taylor_get_answer(message)}
        
            body.update({"to_number": conversation})
            
            maytapi.sendMessage(body)
    else:
        print("Unknow Type:", wttype,  file=sys.stdout, flush=True)
        
    return jsonify({"success": True}), 200