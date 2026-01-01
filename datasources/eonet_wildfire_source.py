# datasources/eonet_wildfire_source.py

from __future__ import annotations

import requests
from datetime import datetime
from typing import List

from datasources.base_source import DataSource, DataSourceError, Event


class EONETWildfireSource(DataSource):
    """
    NASA EONET v3 'wildfires' kategorisindeki orman yangını olaylarını çeker.

    Doküman:
      https://eonet.gsfc.nasa.gov/docs/v3

    Burada:
      - category = wildfires
      - ABD + Kanada için yaklaşık bir bbox kullanıyoruz (DEFAULT_NA_BBOX)
      - days ile kaç gün geriye bakacağımızı kontrol ediyoruz.
    """

    BASE_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"

    # ABD + Kanada için yaklaşık bounding box (lon/lat):
    # min_lon, max_lat, max_lon, min_lat
    DEFAULT_NA_BBOX = "-129.02,50.73,-58.71,12.89"

    def __init__(
        self,
        days: int = 365,
        status: str = "all",
        bbox: str | None = DEFAULT_NA_BBOX,
    ):
        """
        days  : Kaç gün geriye dönük olaylar (EONET 'days' parametresi)
        status: 'open' | 'closed' | 'all'
        bbox  : 'minLon,maxLat,maxLon,minLat' formatında bounding box (opsiyonel)
        """
        self.days = days
        self.status = status
        self.bbox = bbox

    # --- DataSource interface ---

    def fetch_raw(self):
        """
        EONET'ten wildfires kategorisindeki olayları JSON olarak çeker.
        """
        params = {
            "category": "wildfires",
            "days": self.days,
            "status": self.status,
        }

        if self.bbox:
            params["bbox"] = self.bbox

        try:
            r = requests.get(self.BASE_URL, params=params, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise DataSourceError(f"EONET wildfires fetch failed: {e}")

    def parse(self, raw) -> List[Event]:
        """
        EONET Event nesnelerini şu sade formata çeviriyoruz:

        {
            "type": "wildfire",
            "source": "NASA EONET",
            "event_id": ...,
            "title": ...,
            "description": ...,
            "time": datetime | None,
            "latitude": float | None,
            "longitude": float | None,
            "categories": [...],
            "category_ids": [...],
            "category_titles": [...],
            "closed": ...,
            "link": ...,
        }
        """

        events_raw = raw.get("events", [])
        result: List[Event] = []

        for ev in events_raw:
            ev_id = ev.get("id")
            title = ev.get("title")
            description = ev.get("description")
            link = ev.get("link")
            closed = ev.get("closed")

            geometries = ev.get("geometry", [])
            if not geometries:
                continue

            # En son geometri (en güncel nokta)
            last_geom = geometries[-1]
            date_str = last_geom.get("date")
            coords = last_geom.get("coordinates", [])

            lon = coords[0] if len(coords) >= 1 else None
            lat = coords[1] if len(coords) >= 2 else None

            t = self._parse_time(date_str) if date_str else None

            categories = ev.get("categories", []) or []
            category_ids = []
            category_titles = []
            for c in categories:
                if isinstance(c, dict):
                    cid = c.get("id")
                    ctitle = c.get("title")
                    if cid is not None:
                        category_ids.append(cid)
                    if ctitle is not None:
                        category_titles.append(ctitle)

            event: Event = {
                "type": "wildfire",
                "source": "NASA EONET",
                "event_id": ev_id,
                "title": title,
                "description": description,
                "time": t,
                "latitude": lat,
                "longitude": lon,
                "categories": categories,
                "category_ids": category_ids,
                "category_titles": category_titles,
                "closed": closed,
                "link": link,
            }

            result.append(event)

        return result

    # --- yardımcı fonksiyon ---

    @staticmethod
    def _parse_time(date_str: str) -> datetime | None:
        """
        EONET tarih formatı genelde: '2025-12-29T00:00:00Z'
        Bunu datetime'a çeviriyoruz. Hata olursa None döner.
        """
        if not date_str:
            return None
        try:
            if date_str.endswith("Z"):
                date_str = date_str.replace("Z", "+00:00")
            return datetime.fromisoformat(date_str)
        except Exception:
            return None


# Küçük terminal testi
if __name__ == "__main__":
    src = EONETWildfireSource(days=60, status="all")
    raw = src.fetch_raw()
    events = src.parse(raw)
    print(f"{len(events)} wildfire event üretildi.")
    for e in events[:5]:
        print(
            f"- {e.get('time')} | {e.get('title')} | "
            f"({e.get('latitude')}, {e.get('longitude')})"
        )