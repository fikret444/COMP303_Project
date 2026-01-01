# src/fetch_usgs_quakes.py

import requests
from datetime import datetime

from .processing import clean_usgs_earthquake_events
from .storage import save_events_to_json, log_message
from .analytics import (
    load_events_from_json,
    compute_basic_stats,
    count_strong_earthquakes,
    filter_events_in_bbox,
)

USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"


def parse_usgs_geojson(data):
    """
    USGS GeoJSON formatındaki veriyi,
    clean_usgs_earthquake_events fonksiyonunun beklediği ham formata çevirir.

    Dönen her dict şu alanlara sahip olur:
    - type
    - time
    - magnitude
    - location
    - latitude (opsiyonel)
    - longitude (opsiyonel)
    """
    events = []
    features = data.get("features", [])

    for item in features:
        props = item.get("properties", {}) or {}
        geom = item.get("geometry", {}) or {}
        coords = geom.get("coordinates", [None, None, None])

        # USGS time milisaniye (ms) cinsinden epoch olarak gelir
        time_ms = props.get("time")
        time_dt = None
        if isinstance(time_ms, (int, float)):
            time_dt = datetime.fromtimestamp(time_ms / 1000.0)

        event = {
            "type": "earthquake",
            "source": "USGS",
            "location": props.get("place", "Unknown"),
            "magnitude": props.get("mag"),
            "time": time_dt,
            "latitude": coords[1] if len(coords) > 1 else None,
            "longitude": coords[0] if len(coords) > 0 else None,
        }

        events.append(event)

    return events


def main():
    # 1) USGS API'den ham GeoJSON verisini çek
    resp = requests.get(USGS_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # 2) GeoJSON'u ham USGS event listesine parse et
    usgs_raw_events = parse_usgs_geojson(data)
    print(f"🌍 USGS'ten gelen ham event sayısı: {len(usgs_raw_events)}")

    # 3) USGS formatını bizim iç formatımıza göre temizle/normalize et
    cleaned_events = clean_usgs_earthquake_events(usgs_raw_events)
    print(f"✅ Temizlenen event sayısı (dünya geneli): {len(cleaned_events)}")

    # 3.1) Türkiye için bounding box tanımla
    turkey_events = filter_events_in_bbox(
        cleaned_events,
        min_lat=36.0,
        max_lat=42.5,
        min_lon=26.0,
        max_lon=45.0,
    )
    print(f"🇹🇷 Türkiye içindeki event sayısı: {len(turkey_events)}")

    # 4) Sadece Türkiye içindeki event'leri JSON dosyasına kaydet
    if turkey_events:
        save_events_to_json(turkey_events, filename="earthquakes_tr.json")
        log_message(
            f"{len(turkey_events)} USGS deprem event'i (Türkiye) JSON'a kaydedildi."
        )
        print(
            f"💾 {len(turkey_events)} event data/earthquakes_tr.json dosyasına yazıldı."
        )
    else:
        log_message(
            "USGS verisinde Türkiye içinde event bulunamadı.", level="WARNING"
        )
        print("⚠️ USGS verisinde Türkiye içinde event bulunamadı, JSON yazılmadı.")
        return

    # 5) JSON'dan veriyi geri okuyup analitik özet çıkar
    events_from_file = load_events_from_json("earthquakes_tr.json")
    stats = compute_basic_stats(events_from_file)

    if stats is not None:
        strong_quakes = count_strong_earthquakes(events_from_file, threshold=2.5)
        log_message(f"Analitik özet (TR): {stats}", level="INFO")
        log_message(
            f"Türkiye içinde {strong_quakes} adet 2.5 ve üzeri deprem var.", level="INFO"
        )

        print("📊 Analitik özet (TR):", stats)
        print(f"⚠️ Türkiye içinde 2.5 ve üzeri deprem sayısı: {strong_quakes}")
    else:
        log_message("Analiz için yeterli veri yok (TR).", level="WARNING")
        print("⚠️ Analiz için yeterli veri yok.")


if __name__ == "__main__":
    main()