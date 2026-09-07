import os
import sqlite3
from datetime import datetime

import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "leads.db")

BALE_BOT_TOKEN = os.environ.get("BALE_BOT_TOKEN", "")
BALE_CHAT_ID = os.environ.get("BALE_CHAT_ID", "")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            child_age TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_lead(name, phone, child_age):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO leads (name, phone, child_age, created_at) VALUES (?, ?, ?, ?)",
        (name, phone, child_age, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def notify_bale(name, phone, child_age):
    if not BALE_BOT_TOKEN or not BALE_CHAT_ID:
        print("BALE_BOT_TOKEN یا BALE_CHAT_ID ست نشده — پیام ارسال نشد.")
        return

    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendMessage"
    text = (
        "لید جدید ثبت شد ✅\n"
        f"نام: {name}\n"
        f"تماس: {phone}\n"
        f"سن فرزند: {child_age or '-'}"
    )
    try:
        requests.post(url, json={"chat_id": BALE_CHAT_ID, "text": text}, timeout=10)
    except requests.RequestException as e:
        print("ارسال پیام به بله ناموفق بود:", e)


init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    child_age = (data.get("age") or "").strip()

    if not name or not phone:
        return jsonify({"ok": False, "error": "نام و شماره تماس الزامی است"}), 400

    save_lead(name, phone, child_age)
    notify_bale(name, phone, child_age)

    return jsonify({"ok": True})


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
