# datasources/eonet_volcano_source.py

from __future__ import annotations

import requests
from datetime import datetime
from typing import List

from datasources.base_source import DataSource, DataSourceError, Event


class EONETVolcanoSource(DataSource):
    
    BASE_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"

    DEFAULT_AMERICAS_BBOX = "-180,85,-30,-60"

    def __init__(
        self,
        days: int = 365,
        status: str = "all",
        bbox: str | None = DEFAULT_AMERICAS_BBOX,
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
        EONET'ten volcanoes kategorisindeki olayları JSON olarak çeker.
        """
        params = {
            "category": "volcanoes",
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
            raise DataSourceError(f"EONET volcanoes fetch failed: {e}")

    def parse(self, raw) -> List[Event]:
        """
        EONET Event nesnelerini şu sade formata çeviriyoruz:

        {
            "type": "volcano",
            "subtype": "volcanoes",
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
            if not ev_id:
                continue

            # İlk geometry'den koordinat ve tarih al
            geometries = ev.get("geometry", [])
            first_geom = geometries[0] if geometries else {}
            coordinates = first_geom.get("coordinates", [])
            lon = coordinates[0] if len(coordinates) > 0 else None
            lat = coordinates[1] if len(coordinates) > 1 else None

            # İlk tarih
            first_date_str = first_geom.get("date")
            event_time = None
            if first_date_str:
                try:
                    event_time = datetime.fromisoformat(first_date_str.replace("Z", "+00:00"))
                except:
                    pass

            # Son tarih (closed date)
            closed_date = None
            if len(geometries) > 1:
                last_geom = geometries[-1]
                closed_date_str = last_geom.get("date")
                if closed_date_str:
                    try:
                        closed_date = datetime.fromisoformat(closed_date_str.replace("Z", "+00:00"))
                    except:
                        pass

            # Kategoriler
            categories = ev.get("categories", [])
            category_ids = [cat.get("id", "") for cat in categories]
            category_titles = [cat.get("title", "") for cat in categories]

            result.append({
                "type": "volcano",
                "subtype": "volcanoes",
                "source": "NASA EONET",
                "event_id": f"EONET_{ev_id}",
                "title": ev.get("title", ""),
                "description": ev.get("description"),
                "time": event_time.isoformat() if event_time else None,
                "event_time": event_time.isoformat() if event_time else None,
                "latitude": lat,
                "longitude": lon,
                "categories": category_titles,
                "category_ids": category_ids,
                "category_titles": category_titles,
                "closed": closed_date.isoformat() if closed_date else None,
                "link": ev.get("link", ""),
                "status": "closed" if closed_date else "open",
            })

        return result


