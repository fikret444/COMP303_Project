# pipeline/fetch_flood.py

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from datasources.flood_openmeteo_source import OpenMeteoFloodSource
from processing.storage import log_message  # app.log için


# Sel / su taşkını riski yüksek bilinen şehirler (ABD + Kanada)
CITIES = [
    # ABD
    ("New Orleans", 29.9511, -90.0715),
    ("Houston", 29.7604, -95.3698),
    ("Miami", 25.7617, -80.1918),
    ("New York", 40.7128, -74.0060),
    ("Sacramento", 38.5816, -121.4944),

    # Kanada
    ("Vancouver", 49.2827, -123.1207),
    ("Calgary", 51.0447, -114.0719),
    ("Montreal", 45.5019, -73.5674),
    ("Winnipeg", 49.8954, -97.1385),
    ("Toronto", 43.6510, -79.3470),
]


def fetch_flood_risk_for_all_cities() -> List[Dict[str, Any]]:
    """
    CITIES listesindeki her şehir için Open-Meteo Flood API'den
    flood_risk event'leri çeker ve tek listede birleştirir.
    """
    all_events: List[Dict[str, Any]] = []

    for city_name, lat, lon in CITIES:
        print(f"🌊 {city_name} için flood_risk verisi çekiliyor...")
        log_message(f"Flood: {city_name} için flood_risk verisi çekiliyor...")

        src = OpenMeteoFloodSource(
            latitude=lat,
            longitude=lon,
            location_name=city_name,
            past_days=3,
            forecast_days=7,
        )

        raw = src.fetch_raw()
        events = src.parse(raw)
        print(f"   → {city_name} için {len(events)} flood_risk event üretildi.")
        log_message(
            f"Flood: {city_name} için {len(events)} flood_risk event üretildi.",
            level="INFO",
        )

        all_events.extend(events)

    return all_events


def filter_high_risk_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    risk_level'i 'high' olan flood_risk event'lerini filtreler.
    """
    return [
        ev
        for ev in events
        if ev.get("type") == "flood_risk" and ev.get("risk_level") == "high"
    ]


def save_events_to_json(
    all_events: List[Dict[str, Any]],
    high_events: List[Dict[str, Any]],
    filename: str = "flood_risk.json",
) -> Path:
    """
    Tüm flood_risk event'leri ve high risk subset'ini
    tek bir JSON dosyasına yazar (data/flood_risk.json).

    Yapı:
    {
      "generated_at": "...",
      "total_events": N,
      "total_high_risk_events": M,
      "events": [...],
      "high_risk_events": [...]
    }
    """
    root_dir = Path(__file__).resolve().parent.parent
    data_dir = root_dir / "data"
    data_dir.mkdir(exist_ok=True)

    file_path = data_dir / filename

    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d T%H:%M:%S"),
        "total_events": len(all_events),
        "total_high_risk_events": len(high_events),
        "events": all_events,
        "high_risk_events": high_events,
    }

    def default_serializer(obj):
        if isinstance(obj, datetime):
            # Örnek: "2025-12-31 T00:00:00"
            return obj.strftime("%Y-%m-%d T%H:%M:%S")
        raise TypeError(f"Type {type(obj)} is not JSON serializable")

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=default_serializer)

    return file_path


def summarize_flood_risk(events: List[Dict[str, Any]]) -> None:
    """
    Basit bir özet:
    - Her şehir için kaç low/medium/high risk günü var?
    - Maksimum river_discharge değeri nedir?
    """
    summary: Dict[str, Dict[str, Any]] = {}

    for ev in events:
        city = ev.get("location", "Unknown")
        risk = ev.get("risk_level", "unknown")
        discharge = ev.get("river_discharge")

        if city not in summary:
            summary[city] = {
                "low": 0,
                "medium": 0,
                "high": 0,
                "unknown": 0,
                "max_discharge": None,
            }

        # risk sayacını arttır
        if risk not in summary[city]:
            summary[city]["unknown"] += 1
        else:
            summary[city][risk] += 1

        # max_discharge güncelle
        if discharge is not None:
            try:
                d_val = float(discharge)
            except (TypeError, ValueError):
                d_val = None

            if d_val is not None:
                current_max = summary[city]["max_discharge"]
                if current_max is None or d_val > current_max:
                    summary[city]["max_discharge"] = d_val

    print("\n📊 Sel / su taşkını risk özeti (ABD + Kanada şehirleri):")
    log_message(
        "Flood: ABD + Kanada şehirleri için flood_risk özeti oluşturuldu.",
        level="INFO",
    )

    for city, info in summary.items():
        print(f"\n➡ {city}:")
        print(f"   low    : {info['low']}")
        print(f"   medium : {info['medium']}")
        print(f"   high   : {info['high']}")
        if info["max_discharge"] is not None:
            print(f"   max river_discharge: {info['max_discharge']} m³/s")
        else:
            print("   max river_discharge: veri yok")

        # Aynı bilgiyi app.log'a da yaz
        log_message(
            (
                f"Flood summary for {city} → "
                f"low={info['low']}, medium={info['medium']}, "
                f"high={info['high']}, max_discharge={info['max_discharge']}"
            ),
            level="INFO",
        )


def main():
    # 1) Bütün şehirler için flood_risk event'lerini çek
    events = fetch_flood_risk_for_all_cities()
    print(f"\n✅ Toplam {len(events)} flood_risk event üretildi.")
    log_message(
        f"Flood: Toplam {len(events)} flood_risk event üretildi ({len(CITIES)} şehir).",
        level="INFO",
    )

    if not events:
        msg = "Flood: Hiç event gelmedi, JSON'a kaydedilmeyecek."
        print(f"⚠ {msg}")
        log_message(msg, level="WARNING")
        return

    # 2) High risk event'leri filtrele
    high_risk_events = filter_high_risk_events(events)

    # 3) Tek bir dosyaya yaz (data/flood_risk.json)
    file_path = save_events_to_json(events, high_risk_events, filename="flood_risk.json")
    print(f"💾 Flood verisi {file_path} dosyasına kaydedildi.")
    log_message(
        f"Flood: Tüm flood_risk event'ler ve high risk subset {file_path} dosyasına kaydedildi.",
        level="INFO",
    )

    # 4) Basit bir özet yazdır + logla
    summarize_flood_risk(events)


if __name__ == "__main__":
    main()