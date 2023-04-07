import json

# print(f"SYS PATH: {sys.path}")
# sudo lsof -i -P -n | grep LISTEN

from flask import Flask,request
from flask_cors import CORS

from modules import Talk
from modules import Whatsapp
from modules import Firestore
from modules import Sentiment
from modules import MayTapi

app = Flask(__name__)

CORS(app)

whatsapp = Whatsapp()
firestore = Firestore()
symbol_sentiment = Sentiment()
maytapi = MayTapi()

talk = Talk(firestore = firestore)

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
    
@app.route("/whatsapp/send_message", methods=['POST'])
def post_whatsapp_send_message():
    payload = request.form["payload"]

    return maytapi.sendMessage(payload)