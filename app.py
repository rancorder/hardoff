from flask import Flask, jsonify
import threading
from hardoff import main  # hardoff.py の main() を実行

app = Flask(__name__)

@app.route("/")
def home():
    return "Hardoff モニタリングシステムが稼働中！"

@app.route("/start")
def start_monitor():
    thread = threading.Thread(target=main)
    thread.start()
    return jsonify({"message": "監視開始！"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
