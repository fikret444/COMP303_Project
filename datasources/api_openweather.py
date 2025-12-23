import requests
from datetime import datetime
from datasources.base_source import DataSource


class OpenWeatherSource(DataSource):

    def __init__(self, api_key, city):
        self.api_key = api_key
        self.city = city

    def fetch_raw(self):
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": self.city,
            "appid": self.api_key,
            "units": "metric"
        }

        response = requests.get(url, params=params, timeout=10)
        return response.json()

    def parse(self, raw):
        main = raw.get("main", {})
        wind = raw.get("wind", {})
        coord = raw.get("coord", {})

        event = {
            "type": "weather",
            "source": "OpenWeatherMap",
            "location": self.city,
            "temperature": main.get("temp"),
            "wind_speed": wind.get("speed"),
            "humidity": main.get("humidity"),
            "time": datetime.now(),
            "latitude": coord.get("lat"),
            "longitude": coord.get("lon")
        }

        return [event]
