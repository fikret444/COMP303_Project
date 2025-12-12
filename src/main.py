from .storage import save_events_to_csv, log_message
from .processing import clean_earthquake_events
from .analytics import load_events_from_csv, compute_basic_stats, count_strong_earthquakes

def main():
    # Sample Data (it will come from real API/queue)
    raw_events = [
        {
            "id": 1,
            "event_type": "Earthquake",
            "timestamp": "2020-11-30T14:51:00Z",
            "magnitude": "6.9",   # string olarak geldi diyelim
            "location": "İzmir",
        },
        {
            "id": 2,
            "event_type": "earthquake",
            "timestamp": "2023-02-06T03:14:00Z",
            "magnitude": 7.8,
            "location": "Maraş",
        },
        {
            "id": 4,
            "event_type": "earthquake",
            "timestamp": "2023-08-10T19:53:00Z",
            "magnitude": 7.8,
            "location": "Balıkesir",
        },
        {
            "id": 5,
            "event_type": "earthquake",
            "timestamp": "1999-08-19T04:17:00Z",
            "magnitude": 4.7,
            "location": "Kocaeli",
        },
        {
            # HATALI ÖRNEK: magnitude yok
            "id": 3,
            "event_type": "earthquake",
            "timestamp": "2025-12-05T12:10:00Z",
            "location": "Ankara",
        },
    ]

    # 1) Önce veriyi temizle / normalize et
    cleaned_events = clean_earthquake_events(raw_events)

    # 2) Temizlenmiş event'leri kaydet
    if cleaned_events:
        save_events_to_csv(cleaned_events, filename="earthquakes.csv")
        log_message(f"{len(cleaned_events)} tane temiz event CSV'ye kaydedildi.")
    else:
        log_message("Temiz event çıkmadı, CSV'ye yazılmadı.", level="WARNING")

    # Kaydedilen veriden basit analitik özet üret
    events_from_file = load_events_from_csv(filename="earthquakes.csv")
    stats = compute_basic_stats(events_from_file)

    if stats is not None:
        log_message(f"Analitik özet: {stats}", level="INFO")

        #Ek analiz: 5.0 ve üzeri depremleri say
        strong_quakes = count_strong_earthquakes(events_from_file, threshold=5.0)
        log_message(f"5.0 ve üzeri deprem var: {strong_quakes}")
    else:
        log_message("Analiz için yeterli veri yok.", level="WARNING")

if __name__ == "__main__":
    main()