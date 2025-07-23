from flask import Flask, render_template, request
import joblib
from groq import Groq
import requests
import datetime
import sqlite3

import os
# Get the key from environment
os.environ['GROQ_API_KEY'] = os.getenv('groq')
TELEGRAM_BOT_TOKEN = os.getenv("telegram")

conn = sqlite3.connect('user.db')
conn.execute('CREATE TABLE user (name text, timestamp timestamp)')
conn.close()

app = Flask(__name__)

@app.route("/",methods=["GET","POST"])
def index():
    q = request.form.get("q")

    return(render_template("index.html"))

@app.route("/write_log",methods=["GET","POST"])
def write_log():
    user = request.form.get("q")

    # write user and timestamp to log
    timestamp = datetime.datetime.now()
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute('INSERT INTO user (name,timestamp) VALUES(?,?)',(user,timestamp))
    conn.commit()
    c.close()
    conn.close()

    return(render_template("main.html"))

@app.route("/main",methods=["GET","POST"])
def main():
    q = request.form.get("q")

    return(render_template("main.html"))

@app.route("/llama",methods=["GET","POST"])
def llama():
    q = request.form.get("q")
    return(render_template("llama.html"))

@app.route("/llama_reply",methods=["GET","POST"])
def llama_reply():
    q = request.form.get("q")

    client = Groq()
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": q
            }
        ]
    )
    return(render_template("llama_reply.html", r=completion.choices[0].message.content))

@app.route("/deepseek",methods=["GET","POST"])
def deepseek():
    q = request.form.get("q")
    return(render_template("deepseek.html"))

@app.route("/deepseek_reply",methods=["GET","POST"])
def deepseek_reply():
    q = request.form.get("q")

    client = Groq()
    completion_ds = client.chat.completions.create(
        model="deepseek-r1-distill-llama-70b",
        messages=[
            {
                "role": "user",
                "content": "Explain why fast inference is critical for reasoning models"
            }
        ]
    )
    return(render_template("deepseek_reply.html", r=completion_ds.choices[0].message.content))

@app.route("/telegram",methods=["GET","POST"])
def telegram():
    domain_url = "https://for-dbs-fun-1.onrender.com"

    # The following line is used to delete the existing webhook URL for the Telegram bot
    delete_webhook_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
    requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})

    # Set the webhook URL for the Telegram bot
    set_webhook_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={domain_url}/webhook"
    webhook_response = requests.post(set_webhook_url, json={"url": domain_url, "drop_pending_updates": True})

    if webhook_response.status_code == 200:
        # set status message
        status = "The telegram bot is running. Please check with the telegram bot. @dsai_hamster_ft1_bot"
    else:
        status = "Failed to start the telegram bot. Please check the logs."
    return(render_template("telegram.html", status=status))

@app.route("/webhook",methods=["GET","POST"])
def webhook():

    # This endpoint will be called by Telegram when a new message is received
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        # Extract the chat ID and message text from the update
        chat_id = update["message"]["chat"]["id"]
        query = update["message"]["text"]

        # Pass the query to the Groq model
        client = Groq()
        completion_ds = client.chat.completions.create(
            model="deepseek-r1-distill-llama-70b",
            messages=[
                {
                    "role": "user",
                    "content": query
                }
            ]
        )
        response_message = completion_ds.choices[0].message.content

        # Send the response back to the Telegram chat
        send_message_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(send_message_url, json={
            "chat_id": chat_id,
            "text": response_message
        })
    return('ok', 200)

@app.route("/stop_telegram",methods=["GET","POST"])
def stop_telegram():
    domain_url = "https://for-dbs-fun-1.onrender.com"

    # The following line is used to delete the existing webhook URL for the Telegram bot
    delete_webhook_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
    webhook_response = requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})

    if webhook_response.status_code == 200:
        # set status message
        status = "The telegram bot is stopped. Please check with the telegram bot. @dsai_hamster_ft1_bot"
    else:
        status = "Failed to stop the telegram bot. Please check the logs."
    return(render_template("telegram.html", status=status))

@app.route("/dbs",methods=["GET","POST"])
def dbs():
    q = request.form.get("q")
    return(render_template("dbs.html"))

@app.route("/prediction",methods=["GET","POST"])
def prediction():
    q = float(request.form.get("q"))

    # load model
    model = joblib.load("dbs.jl")

    # make prediction
    pred = model.predict([[q]])

    return(render_template("prediction.html",r=pred))

@app.route("/user_log",methods=["GET","POST"])
def user_log():
    q = request.form.get("q")

    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute('''select * from user''')
    rr=""
    for row in c:
        print(row)
        rr = rr + str(row)
    c.close()
    conn.close()

    return(render_template("user_log.html", r=rr))

@app.route("/delete_log",methods=["GET","POST"])
def delete_log():
    q = request.form.get("q")

    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute('DELETE FROM user',);
    conn.commit()
    c.close()
    conn.close()

    return(render_template("delete_log.html"))

if __name__ == "__main__":
    app.run()
