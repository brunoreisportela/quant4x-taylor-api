import os
# import json as simplejson
import json

# print(f"SYS PATH: {sys.path}")
# sudo lsof -i -P -n | grep LISTEN

from flask import Flask,request,render_template
from flask_cors import CORS

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
    start_date = request.args["start_date"]
    end_date = request.args["end_date"]

    return json.dumps(dbController.get_clients(True, start_date, end_date))

# @app.route("/sentiment", methods=['GET'])
# def get_sentiment():
#     index = request.args["index"]
#     return symbol_sentiment.get_status(index)

# @app.route("/lorentzian", methods=['GET'])
# def get_lorentzian():
#     symbol_translate = request.args["symbol"]
#     return firestore.get_lorentzian(symbol_translate)

@app.route("/products/performance", methods=['GET'])
def get_products_performance():
    return get_products_performance_code_local()

@app.route("/bot/message/from/group", methods=['GET'])
def get_bot_message_from_group():
    try:
        return dbController.get_bot_message_from_group()
    except Exception as e:
        return json.dumps({"error": str(e)})

def get_products_performance_code_local():
    return dbController.get_performance_by_code(1)

@app.route("/update/accounts/kpi", methods=['GET'])
def update_accounts_kpi():
    return dbController.update_accounts_kpi()

@app.route("/products/performance/code", methods=['GET'])
def get_products_performance_code():
    code = request.args["code"]
    return dbController.get_internal_performance_by_code(code)

@app.route("/percent/performance/code", methods=['GET'])
def get_percent_performance_code():
    code = request.args["code"]
    return json.dumps(dbController.get_profit_percentage_by_code(code))

# @app.route("/question", methods=['GET'])
# def get_question():
#     question = request.args["question"]

#     if len(question) > 1:
#         return json.dumps(talk.get_response(question))
#     else:
#         return json.dumps("No answer obtained due no question was made.")
    
# @app.route("/account", methods=['GET'])
# def get_account():
#     account_id = request.args["account_id"]
#     from_date = request.args["from_date"]
#     to_date = request.args["to_date"]
#     return json.dumps(firestore.get_account(account_id, from_date, to_date))
    
# @app.route("/news", methods=['GET'])
# def get_news():
#     headers = ["symbol", 'news', 'result']

#     return render_template(
#         'news.html',
#         headers=headers,
#         tableData=newsReader.get_feed_from_FX_street()
#     )

@app.route("/whatsapp/send_message", methods=['POST'])
def post_whatsapp_send_message():
    payload = request.form["payload"]
    return maytapi.sendMessage(payload)


@app.route("/taylor/says", methods=['POST'])
def taylor_says():
    message = request.form["message"]
    return dbController.taylor_says_telegram(message)


@app.route("/client/code", methods=['GET'])
def get_client_code():
    code = request.args["code"]
    return json.dumps(dbController.get_client_by_code(code))