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


WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    80: "Rain showers", 81: "Rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail",
}


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "portfolio-weather/1.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


@app.route("/weather", methods=["GET", "POST"])
def weather():
    weather_data = None
    city = "Accra"

    if request.method == "POST":
        city = request.form.get("city", "").strip() or "Accra"

    try:
        # Step 1: turn the city name into coordinates
        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search?name="
            + urllib.parse.quote(city)
            + "&count=1"
        )
        geo = fetch_json(geo_url)

        if not geo.get("results"):
            flash("City not found. Please check the spelling and try again.", "error")
        else:
            place = geo["results"][0]

            # Step 2: get the current weather for those coordinates
            weather_url = (
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={place['latitude']}&longitude={place['longitude']}"
                "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
            )
            current = fetch_json(weather_url)["current"]

            weather_data = {
                "city": place.get("name", city),
                "country": place.get("country", ""),
                "temp": round(current["temperature_2m"]),
                "desc": WEATHER_CODES.get(current["weather_code"], "Unknown"),
                "humidity": current["relative_humidity_2m"],
                "wind": round(current["wind_speed_10m"]),
            }

    except Exception as e:
        print(f"Weather error: {e}")
        flash("Weather service temporarily unavailable. Please try again.", "error")

    return render_template("weather.html", weather=weather_data)
@app.route("/privacy")
def privacy():
    return render_template("privacy.html") # <-- The filename must be completely lowercase



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
