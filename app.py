from flask import Flask, jsonify, request, render_template

from datasources.usgs_earthquake import USGSEarthquakeSource
from datasources.openweather_source import OpenWeatherSource
from datasources.eonet_source import EONETSource

try:
    from datasources.scraping.scrape_news import scrape_all_risk_headlines
except ImportError:
    def scrape_all_risk_headlines():
        return []

app = Flask(__name__)


@app.get("/")
def home():
    return render_template("dashboard.html")


@app.get("/api/news")
def api_news():
    return jsonify(scrape_all_risk_headlines())


@app.get("/api/earthquakes")
def api_earthquakes():
    src = USGSEarthquakeSource()
    quakes = src.fetch_and_parse()
    return jsonify([q.toDictionary() for q in quakes])


@app.get("/api/weather")
def api_weather():
    city = request.args.get("city", "Istanbul")
    src = OpenWeatherSource(city=city)
    weather_list = src.fetch_and_parse()
    return jsonify([w.toDictionary() for w in weather_list])


@app.get("/api/eonet")
def api_eonet():
    status = request.args.get("status", "all")
    days = int(request.args.get("days", 365))
    limit = int(request.args.get("limit", 50))

    categories_str = request.args.get("categories", "")
    category_ids = [c.strip() for c in categories_str.split(",") if c.strip()]

    bbox_str = request.args.get("bbox", "")
    bbox = None
    if bbox_str:
        parts = [p.strip() for p in bbox_str.split(",")]
        if len(parts) == 4:
            bbox = [float(x) for x in parts]

    src = EONETSource(status=status, days=days, limit=limit, category_ids=category_ids, bbox=bbox)
    events = src.fetch_and_parse()
    return jsonify([e.toDictionary() for e in events])


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
