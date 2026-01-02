# processing/flood_regional_analysis.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from processing.storage import log_message


# Proje kökünü bul (processing klasörünün bir üstü)
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def load_flood_data(filename: str = "flood_risk.json") -> Dict[str, Any] | None:
    """
    data/flood_risk.json dosyasını yükler.
    Eğer dosya yoksa None döner.
    """
    file_path = DATA_DIR / filename

    if not file_path.exists():
        msg = f"Flood regional analysis: {file_path} bulunamadı."
        print(f"⚠ {msg}")
        log_message(msg, level="WARNING")
        return None

    try:
        with file_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        msg = f"Flood regional analysis: {file_path} okunurken hata oluştu: {e}"
        print(f"⚠ {msg}")
        log_message(msg, level="ERROR")
        return None

    return payload


def main():
    payload = load_flood_data("flood_risk.json")
    if payload is None:
        return

    events: List[Dict[str, Any]] = payload.get("events", [])
    generated_at = payload.get("generated_at", "unknown time")

    # Risk seviyelerine göre ayır
    high_events = [e for e in events if e.get("risk_level") == "high"]
    medium_events = [e for e in events if e.get("risk_level") == "medium"]
    low_events = [e for e in events if e.get("risk_level") == "low"]
    unknown_events = [e for e in events if e.get("risk_level") not in ("low", "medium", "high")]

    print("\n🌊 Flood Regional Analysis (ABD + Kanada)")
    print(f"   Üretilme zamanı : {generated_at}")
    print(f"   Toplam event    : {len(events)}")
    print(f"   High risk event : {len(high_events)}")
    print(f"   Medium risk     : {len(medium_events)}")
    print(f"   Low risk        : {len(low_events)}")

    # Şehir bazlı özet
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

    print("\n🏙️ Şehir bazlı flood_risk özeti:")
    for city, info in per_city.items():
        print(f"\n   • {city}:")
        print(f"       low    : {info['low']}")
        print(f"       medium : {info['medium']}")
        print(f"       high   : {info['high']}")
        print(f"       unknown: {info['unknown']}")

    # Küçük yardımcı: örnek eventleri yazdır
    def print_sample_events(label: str, ev_list: List[Dict[str, Any]], max_count: int = 5):
        if not ev_list:
            print(f"\n⚠ {label} için örnek event yok.")
            return

        print(f"\n🌊 {label} flood event örnekleri:")
        for ev in ev_list[:max_count]:
            city = ev.get("location", "Unknown")
            t = ev.get("time", "unknown time")
            discharge = ev.get("river_discharge", "N/A")
            risk = ev.get("risk_level", "unknown")
            print(f"   • {t} | {city} | discharge={discharge} m³/s | risk={risk}")

    # Artık sadece high değil, hepsinden örnek gösteriyoruz
    print_sample_events("HIGH risk", high_events)
    print_sample_events("MEDIUM risk", medium_events)
    print_sample_events("LOW risk", low_events)

    log_message(
        "Flood regional analysis tamamlandı: "
        f"total={len(events)}, high={len(high_events)}, "
        f"medium={len(medium_events)}, low={len(low_events)}",
        level="INFO",
    )


if __name__ == "__main__":
    main()

