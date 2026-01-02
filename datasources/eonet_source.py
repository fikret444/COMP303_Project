from __future__ import annotations

import requests
from datetime import datetime
from typing import List, Optional

from datasources.base_source import DataSource, DataSourceError, Event


class EONETSource(DataSource):
    BASE_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"

    # Whole Americas bbox: [minLon, minLat, maxLon, maxLat]
    DEFAULT_BBOX = [-170.0, -56.0, -34.0, 72.0]

    def __init__(
        self,
        status: str = "open",
        days: int = 30,
        limit: int = 100,
        bbox: Optional[List[float]] = None,
    ):
        self.status = status
        self.days = days
        self.limit = limit
        self.bbox = bbox if bbox is not None else self.DEFAULT_BBOX

    def _convert_bbox_to_string(self, bbox: List[float]) -> str:
        if len(bbox) != 4:
            raise ValueError("Bbox must have 4 elements: [minLon, minLat, maxLon, maxLat]")
        min_lon, min_lat, max_lon, max_lat = bbox
        return f"{min_lon},{max_lat},{max_lon},{min_lat}"

    def fetch_raw(self):
        params = {
            "status": self.status,
            "days": self.days,
            "limit": self.limit,
        }

        if self.bbox:
            params["bbox"] = self._convert_bbox_to_string(self.bbox)

        try:
            r = requests.get(self.BASE_URL, params=params, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise DataSourceError(f"EONET fetch failed: {e}")

    def parse(self, raw) -> List[Event]:
        events_raw = raw.get("events", [])
        result: List[Event] = []

        for ev in events_raw:
            ev_id = ev.get("id")
            if not ev_id:
                continue

            title = ev.get("title", "")
            description = ev.get("description")
            link = ev.get("link", "")

            geometries = ev.get("geometry", [])
            if not geometries:
                continue

            first_geom = geometries[0]
            first_date_str = first_geom.get("date")
            coordinates = first_geom.get("coordinates", [])
            geom_type = first_geom.get("type", "Point")

            lon = None
            lat = None

            if geom_type == "Point" and len(coordinates) >= 2:
                lon = coordinates[0]
                lat = coordinates[1]
            elif geom_type in ["Polygon", "LineString"] and len(coordinates) > 0:
                first_point = coordinates[0] if isinstance(coordinates[0], list) else coordinates
                if len(first_point) >= 2:
                    lon = first_point[0]
                    lat = first_point[1]

            event_time = None
            time_str = None
            if first_date_str:
                try:
                    event_time = datetime.fromisoformat(first_date_str.replace("Z", "+00:00"))
                    time_str = event_time.isoformat()
                except Exception:
                    pass

            closed_date = None
            if len(geometries) > 1:
                last_geom = geometries[-1]
                closed_date_str = last_geom.get("date")
                if closed_date_str:
                    try:
                        closed_date = datetime.fromisoformat(closed_date_str.replace("Z", "+00:00"))
                    except Exception:
                        pass

            categories = ev.get("categories", [])
            category_ids = []
            category_titles = []
            for cat in categories:
                if isinstance(cat, dict):
                    cid = cat.get("id", "")
                    ctitle = cat.get("title", "")
                    if cid:
                        category_ids.append(cid)
                    if ctitle:
                        category_titles.append(ctitle)

            status = "closed" if closed_date else "open"

            event: Event = {
                "type": "natural_event",
                "source": "NASA EONET",
                "event_id": f"EONET_{ev_id}",
                "title": title,
                "description": description,
                "time": datetime.now().isoformat(timespec="seconds"),
                "event_time": time_str,
                "latitude": lat,
                "longitude": lon,
                "categories": category_titles,
                "category_ids": category_ids,
                "category_titles": category_titles,
                "closed": closed_date.isoformat() if closed_date else None,
                "link": link,
                "status": status,
                "geometry_type": geom_type,
            }

            result.append(event)

        return result
