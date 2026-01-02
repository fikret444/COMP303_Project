# pipeline/fetch_volcanoes.py

from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any

from datasources.eonet_volcano_source import EONETVolcanoSource
from processing.storage import save_events_to_json, log_message


def fetch_volcano_events(days: int = 365, status: str = "all") -> List[Dict[str, Any]]:
    """
    NASA EONET'ten (volcanoes kategorisi) son X gün içindeki
    yanardağ olaylarını çeker ve sade event listesi döner.

    EONETVolcanoSource içinde zaten Amerika kıtası (Kuzey + Güney)
    için uygun bbox ayarlı.
    """
    src = EONETVolcanoSource(days=days, status=status)
    raw = src.fetch_raw()
    events = src.parse(raw)
    return events


def summarize_volcano_events(events: List[Dict[str, Any]]) -> None:
    """
    Konsola küçük bir özet basar:
    - Toplam kaç event
    - En güncel birkaç olayı listeler
    """
    total = len(events)
    print(f"🌋 Toplam {total} volcano event alındı.")

    # Zamanı olan event'leri tarihe göre sırala (yeniden eskiye)
    dated_events = [
        e for e in events
        if isinstance(e.get("time"), datetime)
    ]
    dated_events.sort(key=lambda e: e["time"], reverse=True)

    print()
    print("🕒 En güncel 5 yanardağ olayı:")
    for e in dated_events[:5]:
        t = e["time"]
        title = e.get("title") or "İsimsiz olay"
        lat = e.get("latitude")
        lon = e.get("longitude")

        # Zamanı bizim kullandığımız formata benzetelim: 2025-12-23 T19:20:58
        time_str = t.isoformat().replace("T", " T", 1)

        print(f" - {time_str} | {title} | ({lat}, {lon})")


def main() -> None:
    # 1) EONET'ten bütün yanardağ event'lerini çek
    events = fetch_volcano_events(days=365, status="all")

    if not events:
        print("⚠ EONET'ten volcano event gelmedi.")
        log_message("EONET'ten volcano event gelmedi.", level="WARNING")
        return

    # 2) Özet yazdır
    summarize_volcano_events(events)

    # 3) Event'leri JSON'a kaydet (SDEWS/data/volcanoes.json)
    filename = "volcanoes.json"
    save_events_to_json(events, filename=filename)

    log_message(
        f"{len(events)} volcano event EONET'ten alındı ve {filename} dosyasına kaydedildi.",
        level="INFO",
    )
    print(f"\n💾 Event'ler data/{filename} içine kaydedildi.")


if __name__ == "__main__":
    main()