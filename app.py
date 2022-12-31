import json

# print(f"SYS PATH: {sys.path}")
# sudo lsof -i -P -n | grep LISTEN

from flask import Flask,request

from modules import Jack
from modules import Whatsapp

app = Flask(__name__)

# whatsapp = Whatsapp()

@app.route("/")
def service():
    return "Echo"

@app.route("/echo")
def echo():
    return "Echo"