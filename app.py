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


def uv_label(v):
    if v < 3: return "Low"
    if v < 6: return "Moderate"
    if v < 8: return "High"
    if v < 11: return "Very high"
    return "Extreme"


def humidity_label(h):
    if h < 30: return "Low"
    if h <= 60: return "Normal"
    return "High"


def visibility_label(km):
    if km >= 10: return "Good"
    if km >= 4: return "Average"
    return "Poor"


def aqi_label(a):
    if a <= 50: return "Good"
    if a <= 100: return "Moderate"
    if a <= 150: return "Unhealthy for some"
    if a <= 200: return "Unhealthy"
    if a <= 300: return "Very unhealthy"
    return "Hazardous"


def clock(iso_text):
    # "2026-10-30T17:42" -> "5:42 PM"
    return datetime.fromisoformat(iso_text).strftime("%I:%M %p").lstrip("0")


@app.route("/weather", methods=["GET", "POST"])
def weather():
    weather_data = None
    city = "Accra"

    if request.method == "POST":
        city = request.form.get("city", "").strip() or "Accra"

    try:
        # Step 1: city name -> coordinates
        geo = fetch_json(
            "https://geocoding-api.open-meteo.com/v1/search?name="
            + urllib.parse.quote(city) + "&count=1"
        )

        if not geo.get("results"):
            flash("City not found. Please check the spelling and try again.", "error")
        else:
            place = geo["results"][0]
            lat, lon = place["latitude"], place["longitude"]

            # Step 2: current conditions, today's hourly temps, and daily info
            data = fetch_json(
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,"
                "weather_code,visibility,uv_index"
                "&hourly=temperature_2m"
                "&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max"
                "&timezone=auto&forecast_days=1"
            )
            current = data["current"]
            daily = data["daily"]

            # Hourly bars: every 3 hours across today
            times = data["hourly"]["time"]
            temps = data["hourly"]["temperature_2m"]
            picked = [(times[i], temps[i]) for i in range(0, 24, 3)]
            low_t = min(t for _, t in picked)
            high_t = max(t for _, t in picked)
            spread = (high_t - low_t) or 1
            hours = [
                {
                    "label": datetime.fromisoformat(t).strftime("%I %p").lstrip("0"),
                    "temp": round(v),
                    "height": round(25 + 75 * (v - low_t) / spread),
                }
                for t, v in picked
            ]

            # Air quality is a separate API, so a failure here won't break the page
            aqi = None
            try:
                air = fetch_json(
                    "https://air-quality-api.open-meteo.com/v1/air-quality"
                    f"?latitude={lat}&longitude={lon}&current=us_aqi"
                )
                aqi = air["current"].get("us_aqi")
            except Exception as e:
                print(f"Air quality error: {e}")

            temp = round(current["temperature_2m"])
            uv = current.get("uv_index")
            if uv is None:
                uv = daily["uv_index_max"][0]
            uv = round(uv)
            vis_km = round((current.get("visibility") or 0) / 1000, 1)
            humidity = current["relative_humidity_2m"]
            wind = round(current["wind_speed_10m"], 1)

            weather_data = {
                "city": place.get("name", city),
                "country": place.get("country", ""),
                "temp": temp,
                "desc": WEATHER_CODES.get(current["weather_code"], "Unknown"),
                "day_time": datetime.fromisoformat(current["time"]).strftime("%A, %H:%M"),
                "gauge": max(0, min(1, (temp + 20) / 70)),  # -20C to 50C
                "high": round(daily["temperature_2m_max"][0]),
                "low": round(daily["temperature_2m_min"][0]),
                "sunrise": clock(daily["sunrise"][0]),
                "sunset": clock(daily["sunset"][0]),
                "hours": hours,
                "uv": uv,
                "uv_label": uv_label(uv),
                "uv_pct": min(100, round(uv / 12 * 100)),
                "wind": wind,
                "wind_pct": min(100, round(wind / 60 * 100)),
                "humidity": humidity,
                "humidity_label": humidity_label(humidity),
                "visibility": vis_km,
                "visibility_label": visibility_label(vis_km),
                "visibility_pct": min(100, round(vis_km / 20 * 100)),
                "aqi": aqi,
                "aqi_label": aqi_label(aqi) if aqi is not None else "Unavailable",
                "aqi_pct": min(100, round((aqi or 0) / 300 * 100)),
            }

    except Exception as e:
        print(f"Weather error: {e}")
        flash("Weather service temporarily unavailable. Please try again.", "error")

    return render_template("weather.html", weather=weather_data)
@app.route("/privacy")
def privacy():
    return render_template("privacy.html") # <-- The filename must be completely lowercase



if __name__ == '__main__':
    app.run(debug=True)