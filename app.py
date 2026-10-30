@app.route("/weather", methods=["GET", "POST"])
def weather():
    weather_data = None
    city = "Accra"  # Default city
    
    if request.method == "POST":
        city = request.form.get("city", "").strip() or "Accra"
        
    try:
        safe_city = urllib.parse.quote(city)
        # Using a reliable, lightweight alternative format string
        url = f"https://wttr.in{safe_city}?format=j1"
        
        # 🛠️ VERCEL COMPATIBILITY FIX: Supply an absolute browser user-agent to bypass proxy blocks
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            current = data['current_condition'][0]
            nearest = data['nearest_area'][0]
            
            weather_data = {
                "city": nearest['areaName'][0]['value'],
                "country": nearest['country'][0]['value'],
                "temp": current['temp_C'],
                "desc": current['weatherDesc'][0]['value'],
                "humidity": current['humidity'],
                "wind": current['windspeedKmph']
            }
    except Exception as e:
        # Prevent the page from crashing globally if the API fails
        flash("Weather service temporarily unavailable. Please try another city layout.", "error")
        weather_data = None

    return render_template("weather.html", weather=weather_data)
