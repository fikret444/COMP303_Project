from __future__ import annotations

import requests
from datetime import datetime
from typing import List, Optional, Tuple

from datasources.base_source import DataSource, DataSourceError, Event


class EONETSource(DataSource):
    BASE_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"

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
        self.bbox = bbox
    def _bbox_str(self) -> Optional[str]:
        if not self.bbox:
            return None
        if len(self.bbox) != 4:
            raise ValueError("bbox must be [minLon, minLat, maxLon, maxLat]")
        min_lon, min_lat, max_lon, max_lat = self.bbox
        return f"{min_lon},{max_lat},{max_lon},{min_lat}"

    def fetch_raw(self):
        params = {
            "status": self.status,
            "days": self.days,
            "limit": self.limit,
        }

        bbox = self._bbox_str()
        if bbox:
            params["bbox"] = bbox

        try:
            r = requests.get(self.BASE_URL, params=params, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise DataSourceError(f"EONET fetch failed: {e}")

    def _parse_time(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
        except Exception:
            return None

    def _extract_lat_lon(self, geom_type: str, coords) -> Tuple[Optional[float], Optional[float]]:
        if not coords:
            return None, None

        if geom_type == "Point" and len(coords) >= 2:
            return coords[1], coords[0]

        if geom_type in ("Polygon", "LineString"):
            first = coords[0] if isinstance(coords[0], list) else coords
            if len(first) >= 2:
                return first[1], first[0]

        return None, None

    def parse(self, raw) -> List[Event]:
        result: List[Event] = []

        for ev in raw.get("events", []):
            ev_id = ev.get("id")
            geometries = ev.get("geometry") or []
            if not ev_id or not geometries:
                continue

            first_geom = geometries[0]
            geom_type = first_geom.get("type", "Point")
            coords = first_geom.get("coordinates", [])

            lat, lon = self._extract_lat_lon(geom_type, coords)

            event_time = self._parse_time(first_geom.get("date"))
            closed_time = (
                self._parse_time(geometries[-1].get("date"))
                if len(geometries) > 1
                else None
            )

            categories = [c for c in ev.get("categories", []) if isinstance(c, dict)]
            category_ids = [c.get("id") for c in categories if c.get("id")]
            category_titles = [c.get("title") for c in categories if c.get("title")]

            status = "closed" if closed_time else "open"

            result.append({
                "type": "natural_event",
                "source": "NASA EONET",
                "event_id": f"EONET_{ev_id}",
                "title": ev.get("title", ""),
                "description": ev.get("description"),
                "time": event_time,
                "event_time": event_time,
                "latitude": lat,
                "longitude": lon,
                "categories": category_titles,
                "category_ids": category_ids,
                "category_titles": category_titles,
                "closed": closed_time,
                "link": ev.get("link", ""),
                "status": status,
                "geometry_type": geom_type,
            })

        return result
