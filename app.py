import json

# print(f"SYS PATH: {sys.path}")
# sudo lsof -i -P -n | grep LISTEN

from flask import Flask,request

from modules import Talk
from modules import Whatsapp

app = Flask(__name__)

talk = Talk()
# whatsapp = Whatsapp()

@app.route("/")
def service():
    # talk.get_response("What is your name? Tell me about Quant4x.")
    return "Echo"

@app.route("/echo")
def echo():
    return "Echo"