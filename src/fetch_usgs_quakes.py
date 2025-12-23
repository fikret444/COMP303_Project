# src/fetch_usgs_quakes.py

from datasources.usgs_earthquake import USGSEarthquakeSource

from .processing import clean_usgs_earthquake_events
from .storage import save_events_to_json, log_message
from .analytics import (
    load_events_from_json,
    compute_basic_stats,
    count_strong_earthquakes,
    filter_events_in_bbox,
)


def main():
    # 1) USGS kaynağından ham + parse edilmiş deprem verisini çek
    source = USGSEarthquakeSource()

    try:
        usgs_raw_events = source.fetch_and_parse()  # list[dict]
    except Exception as e:
        msg = f"USGS kaynağından veri alınırken hata: {e}"
        log_message(msg, level="ERROR")
        print(f"❌ {msg}")
        return

    print(f"🌍 USGS'ten gelen ham event sayısı: {len(usgs_raw_events)}")

    # 2) USGS formatını bizim iç formatımıza göre temizle/normalize et
    cleaned_events = clean_usgs_earthquake_events(usgs_raw_events)
    print(f"✅ Temizlenen event sayısı (dünya geneli): {len(cleaned_events)}")

    # 3) Türkiye için bounding box ile filtrele
    turkey_events = filter_events_in_bbox(
        cleaned_events,
        min_lat=36.0,
        max_lat=42.5,
        min_lon=26.0,
        max_lon=45.0,
    )
    print(f"🇹🇷 Türkiye sınırları içindeki event sayısı: {len(turkey_events)}")

    # 4) TR event'lerini JSON'a kaydet
    filename = "earthquakes.json"

    if turkey_events:
        save_events_to_json(turkey_events, filename=filename)
        log_message(
            f"{len(turkey_events)} USGS deprem event'i JSON'a kaydedildi.",
            level="INFO",
        )
        print(f"💾 data/{filename} dosyasına yazıldı.")
    else:
        log_message("USGS verisinde Türkiye içinde event bulunamadı.", level="WARNING")
        print("⚠️ USGS verisinde Türkiye içinde event bulunamadı.")
        return

    # 5) Kaydedilen JSON'dan analitik özet çıkar
    events_from_file = load_events_from_json(filename)
    stats = compute_basic_stats(events_from_file)

    if stats is not None:
        # 2.5 ve üzeri depremleri say
        strong_quakes = count_strong_earthquakes(events_from_file, threshold=2.5)
        log_message(f"Analitik özet (TR): {stats}", level="INFO")
        log_message(
            f"Türkiye içinde {strong_quakes} adet 2.5 ve üzeri deprem var.",
            level="INFO",
        )

        print("📊 Analitik özet (TR):", stats)
        print(f"⚠️ Türkiye içinde 2.5 ve üzeri deprem sayısı: {strong_quakes}")
    else:
        log_message("Analiz için yeterli veri yok (TR).", level="WARNING")
        print("⚠️ Analiz için yeterli veri yok.")


if __name__ == "__main__":
    main()