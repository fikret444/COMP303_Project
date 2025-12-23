# src/fetch_openweather.py
#
# OpenWeather API kullanarak tek bir şehir için
# anlık hava durumu bilgisini çeker, temizler ve JSON'a kaydeder.

import os

from datasources.openweather_source import OpenWeatherSource

from .processing import clean_openweather_events
from .storage import save_events_to_json, log_message

# Varsayılan şehir (TR içi bir örnek)
DEFAULT_CITY = "Ankara"


def main():
    # Şehri ister ortam değişkeninden, ister sabitten al
    city = os.getenv("OPENWEATHER_CITY", DEFAULT_CITY)

    # 1) OpenWeather kaynağından ham + parse edilmiş event'leri çek
    try:
        source = OpenWeatherSource(city=city, include_forecast=False)
        raw_events = source.fetch_and_parse()  # list[dict] döner
    except Exception as e:
        msg = f"OpenWeather kaynağından veri alınırken hata: {e}"
        log_message(msg, level="ERROR")
        print(f"❌ {msg}")
        return

    print(f"🌤 {city} için gelen ham event sayısı: {len(raw_events)}")

    # 2) Ham weather event'lerini temizle / normalize et
    cleaned_events = clean_openweather_events(raw_events)
    print(f"✅ Temizlenen hava durumu event sayısı: {len(cleaned_events)}")

    # 3) Temizlenmiş event'leri JSON'a kaydet
    if cleaned_events:
        safe_city = city.replace(",", "_").replace(" ", "_")
        filename = f"openweather_{safe_city}.json"

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