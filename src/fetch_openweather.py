# src/fetch_openweather.py
#
# OpenWeather API kullanarak tek bir şehir için
# anlık hava durumu bilgisini çeker, temizler ve JSON'a kaydeder.

import os
from datetime import datetime

import requests

from .processing import clean_openweather_events
from .storage import save_events_to_json, log_message

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# Örnek şehir: Ankara. İstersen "Istanbul,TR" gibi değiştirebilirsin.
DEFAULT_CITY = "Ankara,TR"

# API key ortam değişkeninden okunuyor
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


def fetch_city_weather(city=DEFAULT_CITY):
    """
    OpenWeather'ın basit weather endpoint'inden
    tek bir şehir için anlık hava durumu çeker.
    """
    if not OPENWEATHER_API_KEY:
        raise RuntimeError(
            "OPENWEATHER_API_KEY ortam değişkeni tanımlı değil. "
            "Lütfen bir OpenWeather API anahtarı ayarlayın."
        )

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }

    resp = requests.get(OPENWEATHER_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    event = {
        "type": "weather",
        "source": "OpenWeatherMap",
        "location": city,
        "temperature": data["main"]["temp"],
        "wind_speed": data["wind"]["speed"],
        "time": datetime.now(),
    }

    return [event]


def main():
    # 1) Ham hava durumu verisini al
    try:
        raw_events = fetch_city_weather()
    except Exception as e:
        msg = f"OpenWeather'dan veri alınamadı: {e}"
        print("⚠️", msg)
        log_message(msg, level="ERROR")
        return

    print(f"⛅ OpenWeather'dan gelen ham event sayısı: {len(raw_events)}")

    # 2) Temizle / normalize et
    cleaned_events = clean_openweather_events(raw_events)
    print(f"✅ Temizlenen event sayısı: {len(cleaned_events)}")

    # 3) JSON'a kaydet
    if cleaned_events:
        filename = "weather_ankara_tr.json"
        save_events_to_json(cleaned_events, filename=filename)
        log_message(
            f"{len(cleaned_events)} adet hava durumu event'i JSON'a kaydedildi ({filename}).",
            level="INFO",
        )
        print(f"💾 data/{filename} dosyasına yazıldı.")
    else:
        log_message(
            "OpenWeather'dan temizlenmiş hava durumu event'i gelmedi.",
            level="WARNING",
        )
        print("⚠️ Temiz event yok, JSON yazılmadı.")


if __name__ == "__main__":
    main()