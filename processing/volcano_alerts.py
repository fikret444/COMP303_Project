# processing/volcano_alerts.py

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from processing.storage import log_message


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def load_volcano_data(filename: str = "volcanoes.json") -> Optional[Dict[str, Any]]:
    file_path = DATA_DIR / filename

    if not file_path.exists():
        msg = f"Volcano alerts: {file_path} bulunamadı."
        print(f"⚠ {msg}")
        log_message(msg, level="WARNING")
        return None

    try:
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        msg = f"Volcano alerts: {file_path} okunurken hata oluştu: {e}"
        print(f"⚠ {msg}")
        log_message(msg, level="ERROR")
        return None


def _safe_parse_time(t: Any) -> Optional[datetime]:
    if not t:
        return None
    if isinstance(t, datetime):
        return t
    if isinstance(t, str):
        try:
            s = t.replace("Z", "+00:00")
            return datetime.fromisoformat(s)
        except Exception:
            return None
    return None


def build_city_alerts(payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    volcanoes.json events listesinden city bazlı risk üretir.
    Eğer eventlerde 'city' yoksa 'location' kullanır.
    """
    events: List[Dict[str, Any]] = payload.get("events", []) or []
    if not events:
        return {}

    now = datetime.now()
    recent_window = now - timedelta(days=30)  # volkan için 30 gün

    per_city_total: Dict[str, int] = {}
    per_city_recent: Dict[str, int] = {}
    per_city_titles: Dict[str, List[str]] = {}

    for ev in events:
        city = ev.get("city") or ev.get("location") or "Unknown"
        per_city_total[city] = per_city_total.get(city, 0) + 1

        t = _safe_parse_time(ev.get("time") or ev.get("event_time"))
        if t and t >= recent_window:
            per_city_recent[city] = per_city_recent.get(city, 0) + 1

        title = (ev.get("title") or "").strip()
        if title:
            per_city_titles.setdefault(city, [])
            if len(per_city_titles[city]) < 5:
                per_city_titles[city].append(title)

    alerts: Dict[str, Dict[str, Any]] = {}

    for city, total_count in per_city_total.items():
        recent_count = per_city_recent.get(city, 0)
        titles = per_city_titles.get(city, [])

        # Basit kural:
        # - recent >= 1 -> high (volkan olayı az ama ciddi)
        # - total >= 2 -> medium
        # - aksi -> low
        if recent_count >= 1:
            level = "high"
            msg = (
                f"{city} için volkanik aktivite riski YÜKSEK. "
                f"Son 30 günde {recent_count} event görülmüş (toplam {total_count})."
            )
        elif total_count >= 2:
            level = "medium"
            msg = (
                f"{city} için orta seviyede volkan riski mevcut. "
                f"Toplam {total_count} event var (son 30 gün: {recent_count})."
            )
        else:
            level = "low"
            msg = (
                f"{city} için düşük seviyede volkan riski görünüyor. "
                f"Toplam {total_count} event var (son 30 gün: {recent_count})."
            )

        alerts[city] = {
            "total_events": total_count,
            "recent_events": recent_count,
            "alert_level": level,
            "message": msg,
            "sample_titles": titles,
        }

    return alerts


def print_alerts(alerts: Dict[str, Dict[str, Any]]) -> None:
    if not alerts:
        print("⚠ Volcano alerts: Şehir bazlı uyarı üretilemedi (boş veri).")
        log_message("Volcano alerts: Şehir bazlı uyarı üretilemedi (boş veri).", level="WARNING")
        return

    print("\n🌋 Volkan Uyarıları (Şehir Bazlı):")
    log_message("Volcano alerts: Şehir bazlı volkan uyarıları oluşturuldu.", level="INFO")

    for city, info in alerts.items():
        level = info["alert_level"]
        msg = info["message"]

        icon = "🟥" if level == "high" else ("🟨" if level == "medium" else "🟩")

        print(f"\n{icon} {city} → [{level.upper()}]")
        print(f"   {msg}")

        titles = info.get("sample_titles", [])
        if titles:
            print("   Örnek başlıklar:")
            for t in titles[:3]:
                print(f"    - {t}")

        log_message(
            f"Volcano alert for {city} → level={level}, recent={info['recent_events']}, total={info['total_events']}",
            level="INFO",
        )


def main():
    payload = load_volcano_data("volcanoes.json")
    if payload is None:
        return

    alerts = build_city_alerts(payload)
    print_alerts(alerts)


if __name__ == "__main__":
    main()
