# pipeline/fetch_flood.py

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from zoneinfo import ZoneInfo

from datasources.flood_openmeteo_source import OpenMeteoFloodSource
from processing.storage import log_message


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


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


def fetch_flood_risk_for_all_cities() -> List[Dict[str, Any]]:
    """
    CITIES listesindeki her şehir için Open-Meteo Flood API'den
    flood_risk event'leri çeker ve tek listede birleştirir.
    """
    all_events: List[Dict[str, Any]] = []

    for city_name, lat, lon in CITIES:
        print(f"🌊 {city_name} için flood_risk verisi çekiliyor...")

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

        all_events.extend(events)

    return all_events


def build_flood_payload(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    flood_regional_analysis.py ve eski flood_report/flood_alerts'in
    beklediği formatta JSON payload üretir:

    {
      "generated_at": "...",
      "total_events": ...,
      "total_high_risk_events": ...,
      "events": [...],
      "high_risk_events": [...]
    }
    """
    # high risk event'leri ayır
    high_events = [
        ev for ev in events
        if ev.get("risk_level") == "high"
    ]

    generated_at = datetime.now(ZoneInfo("Europe/Istanbul")).isoformat()
    generated_at = generated_at.replace("T", " T", 1)

    payload: Dict[str, Any] = {
        "generated_at": generated_at,
        "total_events": len(events),
        "total_high_risk_events": len(high_events),
        "events": events,
        "high_risk_events": high_events,
    }

    return payload


def save_flood_payload(payload: Dict[str, Any], filename: str = "flood_risk.json") -> Path:
    """
    Flood payload'ı data/ klasörüne tek, sabit isimli JSON dosyasına yazar.

    NOT:
    - Her çalıştırmada aynı dosya ÜZERİNE yazıyoruz.
    - İstersen burada timestamp'li arşiv de ekleyebilirsin.
    """
    file_path = DATA_DIR / filename

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

    return file_path


def summarize_flood_risk(payload: Dict[str, Any]) -> None:
    """
    Terminale basit ama daha zengin bir flood özeti yazar:
    - Toplam event
    - High / Medium / Low sayıları
    - Şehir bazlı low/medium/high dağılımı
    """
    events = payload.get("events", [])
    generated_at = payload.get("generated_at", "unknown time")

    # Risk seviyelerine göre ayır
    high_events = [e for e in events if e.get("risk_level") == "high"]
    medium_events = [e for e in events if e.get("risk_level") == "medium"]
    low_events = [e for e in events if e.get("risk_level") == "low"]
    unknown_events = [
        e for e in events
        if e.get("risk_level") not in ("low", "medium", "high")
    ]

    print("\n📊 Sel / su taşkını risk özeti:")
    print(f"   Üretilme zamanı : {generated_at}")
    print(f"   Toplam event    : {len(events)}")
    print(f"   High risk       : {len(high_events)}")
    print(f"   Medium risk     : {len(medium_events)}")
    print(f"   Low risk        : {len(low_events)}")
    if unknown_events:
        print(f"   Unknown risk    : {len(unknown_events)}")

    # Şehir bazlı dağılım
    per_city: Dict[str, Dict[str, int]] = {}

    for ev in events:
        city = ev.get("location", "Unknown")
        risk = ev.get("risk_level", "unknown")

        if city not in per_city:
            per_city[city] = {
                "low": 0,
                "medium": 0,
                "high": 0,
                "unknown": 0,
            }

        if risk not in per_city[city]:
            per_city[city]["unknown"] += 1
        else:
            per_city[city][risk] += 1

    print("\n📍 Şehir bazlı flood_risk özeti:")
    for city, info in per_city.items():
        print(f"\n   • {city}:")
        print(f"       low    : {info['low']}")
        print(f"       medium : {info['medium']}")
        print(f"       high   : {info['high']}")
        print(f"       unknown: {info['unknown']}")


def main():
    # 1) Bütün şehirler için flood_risk event'lerini çek
    events = fetch_flood_risk_for_all_cities()
    print(f"\n✅ Toplam {len(events)} flood_risk event üretildi.")

    if not events:
        msg = "Hiç flood_risk event gelmedi, JSON'a kaydedilmeyecek."
        print(f"⚠ {msg}")
        log_message(f"Flood fetch: {msg}", level="WARNING")
        return

    # 2) Payload hazırla
    payload = build_flood_payload(events)

    # 3) Sabit isimli dosyaya kaydet
    file_path = save_flood_payload(payload, "flood_risk.json")
    print(f"💾 Flood verisi {file_path} dosyasına kaydedildi.")

    log_message(
        f"Flood fetch: {payload['total_events']} event, "
        f"{payload['total_high_risk_events']} high risk gün kaydedildi.",
        level="INFO",
    )

    # 4) Küçük özet
    summarize_flood_risk(payload)


if __name__ == "__main__":
    main()