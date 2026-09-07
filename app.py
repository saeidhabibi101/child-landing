import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "leads.db")

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "")


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


def notify_email(name, phone, child_age):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD or not NOTIFY_EMAIL:
        print("تنظیمات ایمیل کامل نیست — ایمیل ارسال نشد.")
        return

    body = (
        "لید جدید ثبت شد\n\n"
        f"نام: {name}\n"
        f"تماس: {phone}\n"
        f"سن فرزند: {child_age or '-'}"
    )
    msg = MIMEText(body)
    msg["Subject"] = "لید جدید - مشاوره کودک"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = NOTIFY_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print("ارسال ایمیل ناموفق بود:", e)


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
    notify_email(name, phone, child_age)

    return jsonify({"ok": True})


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
