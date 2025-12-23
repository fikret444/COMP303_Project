from flask import Flask, jsonify, request

from datasources.usgs_earthquake import USGSEarthquakeSource
from datasources.openweather_source import OpenWeatherSource

# your scraping (adjust path to your project) - opsiyonel (lxml gerektirir)
try:
    from datasources.scraping.scrape_news import scrape_all_risk_headlines
except ImportError:
    def scrape_all_risk_headlines():
        return []

app = Flask(__name__)


@app.get("/")
def home():
    return "Disaster Early Warning System is running."


@app.get("/api/news")
def api_news():
    return jsonify(scrape_all_risk_headlines())


@app.get("/api/earthquakes")
def api_earthquakes():
    src = USGSEarthquakeSource()
    return jsonify(src.fetch_and_parse())


@app.get("/api/weather")
def api_weather():
    city = request.args.get("city", "Istanbul")
    src = OpenWeatherSource(city=city)
    return jsonify(src.fetch_and_parse())


if __name__ == "__main__":
    app.run(debug=True)
