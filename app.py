import json
import os
import yfinance as yf

# print(f"SYS PATH: {sys.path}")
# sudo lsof -i -P -n | grep LISTEN

from flask import Flask,request,render_template
from flask_table import Table, Col
from flask_cors import CORS

from modules import Talk
from modules import Whatsapp
from modules import Firestore
from modules import Sentiment
from modules import MayTapi
from modules import NewsReader

app = Flask(__name__)

os.environ["OPENAI_API_KEY"] = "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"

CORS(app)

whatsapp = Whatsapp()
firestore = Firestore()
symbol_sentiment = Sentiment()
maytapi = MayTapi()

talk = Talk(firestore = firestore)
newsReader = NewsReader()

class ItemTable(Table):
    news = Col('news')
    result = Col('result')

@app.route("/")
def get_service():
    return "Echo"

@app.route("/echo")
def get_echo():
    return "Echo"

@app.route("/accounts", methods=['GET'])
def get_accounts():
    return json.dumps(firestore.get_accounts())

@app.route("/sentiment", methods=['GET'])
def get_sentiment():
    index = request.args["index"]
    return symbol_sentiment.get_status(index)

@app.route("/lorentzian", methods=['GET'])
def get_lorentzian():
    symbol_translate = request.args["symbol"]
    return firestore.get_lorentzian(symbol_translate)

@app.route("/products/performance", methods=['GET'])
def get_products_performance():
    return json.dumps(firestore.get_products_performance())

@app.route("/question", methods=['GET'])
def get_question():
    question = request.args["question"]

    if len(question) > 1:
        return json.dumps(talk.get_response(question))
    else:
        return json.dumps("No answer obtained due no question was made.")
    
@app.route("/news", methods=['GET'])
def get_news():
    # yfi = yf.Ticker("GBPUSD=X")
    table = ItemTable(newsReader.get_feed())
    return table.__html__()
    # return render_template("news.html", table=table)
    # return json.dumps(newsReader.get_response(yfi.news[index]["title"]))

@app.route("/whatsapp/send_message", methods=['POST'])
def post_whatsapp_send_message():
    payload = request.form["payload"]

    return maytapi.sendMessage(payload)