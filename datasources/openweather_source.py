import requests
from datetime import datetime
import os

from datasources.base_source import DataSource, DataSourceError

# config.py'den API key'i al, yoksa environment variable'dan dene
try:
    from config import OPENWEATHER_API_KEY as CONFIG_API_KEY
except ImportError:
    CONFIG_API_KEY = None


class OpenWeatherSource(DataSource):
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"  # 5 günlük, 3 saatlik tahmin

    def __init__(self, city="Istanbul", include_forecast=False):
        self.city = city
        self.include_forecast = include_forecast
        # Önce config.py'den, sonra environment variable'dan, son olarak boş string
        self.api_key = CONFIG_API_KEY or os.getenv("OPENWEATHER_API_KEY", "")

    def fetch_raw(self):
        if not self.api_key:
            raise DataSourceError("OPENWEATHER_API_KEY is missing. Set it in config.py or as environment variable.")

        params = {
            "q": f"{self.city},TR",
            "appid": self.api_key,
            "units": "metric",
        }

        try:
            # Anlık hava durumu
            r = requests.get(self.BASE_URL, params=params, timeout=10)
            r.raise_for_status()
            current_data = r.json()
            
            # Forecast verisi de isteniyorsa çek
            forecast_data = None
            if self.include_forecast:
                try:
                    r_forecast = requests.get(self.FORECAST_URL, params=params, timeout=10)
                    r_forecast.raise_for_status()
                    forecast_data = r_forecast.json()
                except Exception as e:
                    # Forecast başarısız olsa bile current data'yı döndür
                    pass
            
            return {
                "current": current_data,
                "forecast": forecast_data
            }
        except Exception as e:
            raise DataSourceError(f"OpenWeather fetch failed: {e}")

    def parse(self, raw):
        # raw artık {"current": {...}, "forecast": {...}} formatında
        current_data = raw.get("current", raw)  # Eski format desteği için
        forecast_data = raw.get("forecast")
        
        main = current_data.get("main", {})
        wind = current_data.get("wind", {})
        coord = current_data.get("coord", {})
        weather_list = current_data.get("weather", [{}])
        weather_info = weather_list[0] if weather_list else {}
        clouds = current_data.get("clouds", {})
        sys_info = current_data.get("sys", {})
        rain = current_data.get("rain", {})
        snow = current_data.get("snow", {})
        
        # Yağış bilgisini al (1h veya 3h değeri varsa)
        precipitation = 0
        if rain:
            precipitation = rain.get("1h", rain.get("3h", 0))
        elif snow:
            precipitation = snow.get("1h", snow.get("3h", 0))
        
        result = [{
            "type": "weather",
            "source": "OpenWeatherMap",
            "location": self.city,
            "temperature": main.get("temp"),
            "feels_like": main.get("feels_like"),
            "temp_min": main.get("temp_min"),
            "temp_max": main.get("temp_max"),
            "humidity": main.get("humidity"),
            "pressure": main.get("pressure"),
            "wind_speed": wind.get("speed"),
            "wind_direction": wind.get("deg"),
            "wind_gust": wind.get("gust"),
            "clouds": clouds.get("all", 0),
            "precipitation": precipitation,
            "visibility": current_data.get("visibility"),
            "weather_main": weather_info.get("main", ""),
            "weather_description": weather_info.get("description", ""),
            "weather_icon": weather_info.get("icon", ""),
            "sunrise": sys_info.get("sunrise"),
            "sunset": sys_info.get("sunset"),
            "time": datetime.now(),
            "latitude": coord.get("lat"),
            "longitude": coord.get("lon"),
        }]
        
        # Forecast verisi varsa parse et ve ekle
        if forecast_data and forecast_data.get("list"):
            forecast_list = []
            for item in forecast_data.get("list", []):
                item_main = item.get("main", {})
                item_wind = item.get("wind", {})
                item_weather = item.get("weather", [{}])[0] if item.get("weather") else {}
                
                # Forecast timestamp'ini datetime'a çevir
                forecast_time = datetime.fromtimestamp(item.get("dt", 0))
                
                forecast_list.append({
                    "type": "weather_forecast",
                    "source": "OpenWeatherMap",
                    "location": self.city,
                    "forecast_time": forecast_time.isoformat(),
                    "temperature": item_main.get("temp"),
                    "feels_like": item_main.get("feels_like"),
                    "temp_min": item_main.get("temp_min"),
                    "temp_max": item_main.get("temp_max"),
                    "humidity": item_main.get("humidity"),
                    "pressure": item_main.get("pressure"),
                    "wind_speed": item_wind.get("speed"),
                    "wind_direction": item_wind.get("deg"),
                    "wind_gust": item_wind.get("gust"),
                    "clouds": item.get("clouds", {}).get("all", 0),
                    "weather_main": item_weather.get("main", ""),
                    "weather_description": item_weather.get("description", ""),
                    "weather_icon": item_weather.get("icon", ""),
                    "precipitation": item.get("rain", {}).get("3h", 0) or item.get("snow", {}).get("3h", 0),
                    "latitude": coord.get("lat"),
                    "longitude": coord.get("lon"),
                })
            
            result.extend(forecast_list)
        
        return result
