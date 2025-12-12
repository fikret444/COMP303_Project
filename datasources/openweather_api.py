import requests
from datetime import datetime
from datasources.base_source import DataSource


class OpenWeatherSource(DataSource):
    def __init__(self, api_key, city):
        self.api_key = api_key
        self.city = city

    def fetch_events(self):
        url = "https://api.openweathermap.org/data/2.5/weather"

        params = {
            "q": self.city,
            "appid": self.api_key,
            "units": "metric",
        }

        response = requests.get(url, params=params)
        data = response.json()

        event = {
            "type": "weather",
            "source": "OpenWeatherMap",
            "location": self.city,
            "temperature": data["main"]["temp"],
            "wind_speed": data["wind"]["speed"],
            "time": datetime.now(),
        }

        return [event]
