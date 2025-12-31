# processing/flood_report.py

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
        msg = f"Flood report: {file_path} bulunamadı."
        print(f"⚠ {msg}")
        log_message(msg, level="WARNING")
        return None

    with file_path.open("r", encoding="utf-8") as f:
        try:
            payload = json.load(f)
        except Exception as e:
            msg = f"Flood report: {file_path} okunurken hata oluştu: {e}"
            print(f"⚠ {msg}")
            log_message(msg, level="ERROR")
            return None

    return payload


def print_high_risk_summary(payload: Dict[str, Any]) -> None:
    """
    flood_risk.json içinden high_risk_events listesini alır,
    şehir bazlı özet ve tek tek event listesi basar.
    """
    events: List[Dict[str, Any]] = payload.get("events", [])
    high_events: List[Dict[str, Any]] = payload.get("high_risk_events", [])

    total = payload.get("total_events", len(events))
    total_high = payload.get("total_high_risk_events", len(high_events))
    generated_at = payload.get("generated_at", "unknown time")

    print("\n🧾 Flood Risk Raporu")
    print(f"   Üretilme zamanı : {generated_at}")
    print(f"   Toplam event    : {total}")
    print(f"   High risk event : {total_high}")

    if not high_events:
        msg = "Flood report: High risk flood event bulunamadı."
        print("\n✅ Şu an için high risk flood_risk event yok.")
        log_message(msg, level="INFO")
        return

    # Şehir bazlı high risk sayıları
    per_city: Dict[str, int] = {}
    for ev in high_events:
        city = ev.get("location", "Unknown")
        per_city[city] = per_city.get(city, 0) + 1

    print("\n📍 High risk sel/gün sayısı (şehir bazlı):")
    for city, count in per_city.items():
        print(f"   - {city}: {count} gün high risk")

    # Tek tek event'leri yazdıralım (istersen burada limitleyebilirsin)
    print("\n🔎 High risk flood event detayları:")
    for ev in high_events:
        city = ev.get("location", "Unknown")
        t = ev.get("time", "unknown time")
        discharge = ev.get("river_discharge", "N/A")
        risk = ev.get("risk_level", "unknown")

        print(f"   • {t} | {city} | discharge={discharge} m³/s | risk={risk}")

    log_message(
        f"Flood report: {len(high_events)} adet high risk flood event raporlandı.",
        level="INFO",
    )


def main():
    payload = load_flood_data("flood_risk.json")
    if payload is None:
        return

    print_high_risk_summary(payload)


if __name__ == "__main__":
    main()