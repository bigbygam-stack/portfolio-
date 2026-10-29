import os
import sqlite3
import json
import urllib.request
import urllib.parse
from datetime import datetime
from flask import Flask, flash, g, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-before-deploying")

# 🛠️ FIX 1: Vercel serverless environments only allow file writing inside the /tmp directory
if os.environ.get("VERCEL"):
    DATABASE = "/tmp/messages.db"
else:
    DATABASE = os.path.join(os.path.dirname(__file__), "messages.db")

# Edit this list to show your own work.
PROJECTS = [
    {
        "title": "Expense Tracker",
        "description": "A Flask app to log spending and see monthly totals.",
        "tags": ["Python", "Flask", "SQLite"],
        "link": "#",
    },
    {
        "title": "Weather Dashboard",
        "description": "Live weather cards powered by a public API.",
        "tags": ["Python", "API", "CSS"],
        "link": "/weather",  # Linked to our functional route
    },
    {
        "title": "Quiz Game",
        "description": "Multiple-choice quiz with scoring and feedback.",
        "tags": ["HTML", "CSS", "Python"],
        "link": "#",
    },
]

SKILLS = ["Python", "Flask", "HTML", "CSS", "SQLite", "Git"]


def init_db(db):
    """Creates the database schema safely inside the active database connection."""
    db.execute(
        """CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )
    db.commit()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        # 🛠️ FIX 2: Initialize the table inside /tmp dynamically right after connecting
        init_db(g.db)
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/")
def index():
    # 🛠️ FIX 3: Replaced 'index.html' with your actual 'home.html' layout file name
    return render_template("home.html", projects=PROJECTS, skills=SKILLS)


@app.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not message or "@" not in email:
        flash("Please fill in every field with a valid email.", "error")
        return redirect(url_for("index") + "#contact")

    db = get_db()
    db.execute(
        "INSERT INTO messages (name, email, message, created_at) VALUES (?, ?, ?, ?)",
        (name, email, message, datetime.now().isoformat(timespec="seconds")),
    )
    db.commit()
    flash("Thanks! Your message was sent.", "success")
    return redirect(url_for("index") + "#contact")


@app.route("/messages")
def messages():
    """Simple inbox. Protect or remove this route before going public."""
    rows = get_db().execute(
        "SELECT * FROM messages ORDER BY id DESC"
    ).fetchall()
    return render_template("messages.html", messages=rows)


@app.route("/weather", methods=["GET", "POST"])
def weather():
    weather_data = None
    city = "Accra"  # Default city
    
    if request.method == "POST":
        city = request.form.get("city", "").strip() or "Accra"
        
    try:
        safe_city = urllib.parse.quote(city)
        url = f"https://wttr.in{safe_city}?format=j1"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            current = data['current_condition'][0]
            weather_data = {
                "city": data['nearest_area'][0]['areaName'][0]['value'],
                "country": data['nearest_area'][0]['country'][0]['value'],
                "temp": current['temp_C'],
                "desc": current['weatherDesc'][0]['value'],
                "humidity": current['humidity'],
                "wind": current['windspeedKmph']
            }
    except Exception as e:
        flash("Could not look up weather for that location. Please try another city.", "error")

    return render_template("weather.html", weather=weather_data)


# 🛠️ FIX 4: Removed global init_db() call. The app execution flow is now totally clean.

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
