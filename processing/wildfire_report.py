# processing/wildfire_report.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from processing.storage import log_message


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def load_wildfire_data(filename: str = "wildfires.json") -> Optional[Dict[str, Any]]:
    """
    data/wildfires.json dosyasını yükler.
    Beklenen format:
    {
      "generated_at": "...",
      "total_events": ...,
      "events": [ {...}, {...}, ... ]
    }
    """
    file_path = DATA_DIR / filename

    if not file_path.exists():
        msg = f"Wildfire report: {file_path} bulunamadı."
        print(f"⚠ {msg}")
        log_message(msg, level="WARNING")
        return None

    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        msg = f"Wildfire report: {file_path} okunurken hata oluştu: {e}"
        print(f"⚠ {msg}")
        log_message(msg, level="ERROR")
        return None


def summarize_wildfires(payload: Dict[str, Any]) -> None:
    """
    Wildfire verisinden şehir bazlı özet üretir:
      - Her şehir için kaç wildfire olayı var
      - Örnek başlıklar
      - Şehre atanamayan event sayısı
    """
    events: List[Dict[str, Any]] = payload.get("events", [])
    generated_at: str = payload.get("generated_at", "bilinmiyor")
    total_events: int = payload.get("total_events", len(events))

    if not events:
        print("⚠ Wildfire report: Event listesi boş.")
        log_message("Wildfire report: Event listesi boş.", level="WARNING")
        return

    print("\n🧾 Orman Yangını (Wildfires) Raporu")
    print(f"   Üretilme zamanı : {generated_at}")
    print(f"   Toplam event    : {total_events}")

    log_message(
        f"Wildfire report: generated_at={generated_at}, total_events={total_events}",
        level="INFO",
    )

    per_city: Dict[str, Dict[str, Any]] = {}
    no_city_events: List[Dict[str, Any]] = []

    for ev in events:
        city = ev.get("city")
        title = ev.get("title", "(başlık yok)")
        time_str = ev.get("time")

        if city is None:
            no_city_events.append(ev)
            continue

        if city not in per_city:
            per_city[city] = {
                "count": 0,
                "samples": [],
            }

        info = per_city[city]
        info["count"] += 1

        # Örnek olaylardan birkaç tanesini topla
        if len(info["samples"]) < 5:
            info["samples"].append((time_str, title))

    if not per_city:
        print("\n📍 Şehir bazlı atanmış orman yangını olayı yok.")
        log_message("Wildfire report: Şehir bazlı atanmış event yok.", level="WARNING")
    else:
        print("\n📍 Şehir bazlı orman yangını özeti:")
        for city, info in per_city.items():
            print(f"\n   • {city}: {info['count']} wildfire event")
            if info["samples"]:
                print("     Örnek olaylar:")
                for t, title in info["samples"]:
                    print(f"       - {t} | {title}")
            log_message(
                f"Wildfire report city={city}, count={info['count']}",
                level="INFO",
            )

    if no_city_events:
        print(
            f"\nℹ Şehre atanamayan {len(no_city_events)} event var "
            "(CITIES listesindeki şehirlere 1000 km'den uzak)."
        )
        log_message(
            f"Wildfire report: Şehre atanamayan event sayısı = {len(no_city_events)}",
            level="INFO",
        )


def main():
    payload = load_wildfire_data("wildfires.json")
    if payload is None:
        return
    summarize_wildfires(payload)


if __name__ == "__main__":
    main()

