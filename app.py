import os
import sqlite3
import json
import urllib.request
import urllib.parse
from datetime import datetime
from flask import Flask, flash, g, redirect, render_template, request, url_for

# 🛠️ CRITICAL VERCEL ENTRY POINT: Do not move or modify this line!
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-before-deploying")

# Vercel serverless environments only allow file writing inside the /tmp directory
if os.environ.get("VERCEL"):
    DATABASE = "/tmp/messages.db"
else:
    DATABASE = os.path.join(os.path.dirname(__file__), "messages.db")

# Portfolio data list
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
        "link": "/weather",
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
        init_db(g.db)
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/")
def index():
    return render_template("index.html", projects=PROJECTS, skills=SKILLS)


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
    rows = get_db().execute("SELECT * FROM messages ORDER BY id DESC").fetchall()
    return render_template("messages.html", messages=rows)

@app.route("/weather", methods=["GET", "POST"])
@app.route("/weather", methods=["GET", "POST"])
def weather():
    weather_data = None
    city = "Accra"
    
    if request.method == "POST":
        city = request.form.get("city", "").strip() or "Accra"
        
    try:
        safe_city = urllib.parse.quote(city.strip())
        url = f"https://wttr.in{safe_city}?format=j1"
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            raw_json = response.read().decode('utf-8')
            data = json.loads(raw_json)
            
            # 🛠️ FIX: Safely verify arrays exist and extract the first dictionary index [0]
            if 'current_condition' in data and len(data['current_condition']) > 0 and 'nearest_area' in data and len(data['nearest_area']) > 0:
                current = data['current_condition'][0]
                nearest = data['nearest_area'][0]
                
                weather_data = {
                    "city": nearest.get('areaName', [{}])[0].get('value', city),
                    "country": nearest.get('country', [{}])[0].get('value', ''),
                    "temp": current.get('temp_C', 'N/A'),
                    "desc": current.get('weatherDesc', [{}])[0].get('value', 'Unknown'),
                    "humidity": current.get('humidity', 'N/A'),
                    "wind": current.get('windspeedKmph', 'N/A')
                }
            else:
                flash("Location data structure format not recognized.", "error")
                
    except Exception as e:
        print(f"DEPLOYMENT DIAGNOSTIC ENGINE LOG: {str(e)}")
        flash("Weather service temporarily unavailable. Please verify the city spelling and try again.", "error")
        weather_data = None

    return render_template("weather.html", weather=weather_data)
@app.route("/privacy")
def privacy():
    return render_template("privacy.html") # <-- The filename must be completely lowercase



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
