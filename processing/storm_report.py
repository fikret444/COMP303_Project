# processing/storm_report.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from processing.storage import log_message


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def load_storm_data(filename: str = "storms.json") -> Optional[Dict[str, Any]]:
    """
    data/storms.json dosyasını yükler.
    Beklenen format:
    {
      "generated_at": "...",
      "total_events": ...,
      "events": [ {...}, {...}, ... ]
    }
    """
    file_path = DATA_DIR / filename

    if not file_path.exists():
        msg = f"Storm report: {file_path} bulunamadı."
        print(f"⚠ {msg}")
        log_message(msg, level="WARNING")
        return None

    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        msg = f"Storm report: {file_path} okunurken hata oluştu: {e}"
        print(f"⚠ {msg}")
        log_message(msg, level="ERROR")
        return None

    return data


def summarize_storms(payload: Dict[str, Any]) -> None:
    """
    storms.json içindeki veriden şehir bazlı özet üretir:
      - Her şehir için kaç olay var
      - Şehre atanamayan event sayısı
      - Örnek başlıklar
    """

    events: List[Dict[str, Any]] = payload.get("events", [])
    generated_at: str = payload.get("generated_at", "bilinmiyor")
    total_events: int = payload.get("total_events", len(events))

    if not events:
        print("⚠ Storm report: Event listesi boş.")
        log_message("Storm report: Event listesi boş.", level="WARNING")
        return

    print("\n🧾 Storm (Severe Storms) Raporu")
    print(f"   Üretilme zamanı : {generated_at}")
    print(f"   Toplam event    : {total_events}")

    log_message(
        f"Storm report: generated_at={generated_at}, total_events={total_events}",
        level="INFO",
    )

    # Şehir bazlı sayım
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
                "titles": [],
            }

        info = per_city[city]
        info["count"] += 1

        # Örnek başlıklardan ilk birkaçını toplayalım
        if len(info["titles"]) < 5:
            info["titles"].append((time_str, title))

    # Şehir bazlı özet
    if not per_city:
        print("\n📍 Şehir bazlı atanmış event yok.")
        log_message("Storm report: Şehir bazlı atanmış event yok.", level="WARNING")
    else:
        print("\n📍 Şehir bazlı fırtına özeti:")
        for city, info in per_city.items():
            print(f"\n   • {city}: {info['count']} storm event")
            if info["titles"]:
                print("     Örnek olaylar:")
                for t, title in info["titles"]:
                    print(f"       - {t} | {title}")
            log_message(
                f"Storm report city={city}, count={info['count']}",
                level="INFO",
            )

    # Şehre atanamayan event'ler
    if no_city_events:
        print(
            f"\nℹ Şehre atanamayan {len(no_city_events)} event var "
            "(CITIES listesindeki şehirlere 500 km'den uzak)."
        )
        log_message(
            f"Storm report: Şehre atanamayan event sayısı = {len(no_city_events)}",
            level="INFO",
        )


def main():
    payload = load_storm_data("storms.json")
    if payload is None:
        return

    summarize_storms(payload)


if __name__ == "__main__":
    main()

