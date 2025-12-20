import requests
from datetime import datetime
import os

from datasources.base_source import DataSource, DataSourceError


class OpenWeatherSource(DataSource):
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, city="Istanbul"):
        self.city = city
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "")

    def fetch_raw(self):
        if not self.api_key:
            raise DataSourceError("OPENWEATHER_API_KEY is missing (set env variable).")

        params = {
            "q": f"{self.city},TR",
            "appid": self.api_key,
            "units": "metric",
        }

        try:
            r = requests.get(self.BASE_URL, params=params, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise DataSourceError(f"OpenWeather fetch failed: {e}")

    def parse(self, raw):
        main = raw.get("main", {})
        wind = raw.get("wind", {})
        coord = raw.get("coord", {})

        return [{
            "type": "weather",
            "source": "OpenWeatherMap",
            "location": self.city,
            "temperature": main.get("temp"),
            "humidity": main.get("humidity"),
            "wind_speed": wind.get("speed"),
            "time": datetime.now(),
            "latitude": coord.get("lat"),
            "longitude": coord.get("lon"),
        }]
