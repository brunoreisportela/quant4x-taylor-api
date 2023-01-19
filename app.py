import json

# print(f"SYS PATH: {sys.path}")
# sudo lsof -i -P -n | grep LISTEN

from flask import Flask,request
from flask_cors import CORS

from modules import Talk
from modules import Whatsapp
from modules import Firestore

app = Flask(__name__)

CORS(app)

# whatsapp = Whatsapp()
talk = Talk()

@app.route("/")
def service():
    return "Echo"

@app.route("/echo")
def echo():
    return "Echo"

@app.route("/question", methods=['GET'])
def question():
    question = request.args["question"]

    if len(question) > 1:
        return json.dumps(talk.get_response(question))
    else:
        return json.dumps("No answer obtained due no question was made.")