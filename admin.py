from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import sqlite3
import hashlib
import requests
from config import TELEGRAM_BOT_TOKEN

app = Flask(__name__)
app.secret_key = "super_secret_key_change_later"  # required for sessions

UPLOAD_FOLDER = "uploads"


def get_db():
    conn = sqlite3.connect("grievance.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM admins WHERE username=? AND password_hash=?",
            (username, password_hash)
        )
        admin = cur.fetchone()

        if admin:
            session["admin_logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- PROTECTED DASHBOARD ----------------
@app.route("/")
def dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM grievances")
    grievances = cur.fetchall()
    return render_template("admin.html", grievances=grievances)


# ---------------- UPDATE STATUS ----------------
@app.route("/update_status", methods=["POST"])
def update_status():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    grievance_id = request.form["grievance_id"]
    new_status = request.form["status"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE grievances SET status=? WHERE grievance_id=?",
        (new_status, grievance_id)
    )
    conn.commit()

    return redirect(url_for("dashboard"))


# ---------------- VIEW IMAGE ----------------
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    return send_from_directory(UPLOAD_FOLDER, filename)


# ---------------- SEND MESSAGE TO USER ----------------
def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)


@app.route("/send_message", methods=["POST"])
def send_message():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    chat_id = request.form["chat_id"]
    message = request.form["message"]

    send_telegram_message(chat_id, message)
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(port=8000, debug=True)
