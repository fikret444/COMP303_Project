import requests
from datetime import datetime

from datasources.base_source import DataSource, DataSourceError
from models import NaturalEvent


class EONETSource(DataSource):
    BASE_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"
    GEOJSON_URL = "https://eonet.gsfc.nasa.gov/api/v3/events/geojson"

    def __init__(self, status="open", days=30, limit=50, category_ids=None, bbox=None):
        self.status = status
        self.days = days
        self.limit = limit
        self.category_ids = category_ids or []
        self.bbox = bbox  # IMPORTANT: [upperLeftLon, upperLeftLat, lowerRightLon, lowerRightLat]

    def fetch_raw(self):
        params = {
            "status": self.status,
            "limit": self.limit
        }

        if self.days is not None:
            params["days"] = self.days

        if self.category_ids:
            params["category"] = ",".join(self.category_ids)

        if self.bbox and len(self.bbox) == 4:
            params["bbox"] = ",".join(str(x) for x in self.bbox)

        # If bbox is used, EONET expects it on the GeoJSON endpoint
        url = self.GEOJSON_URL if self.bbox else self.BASE_URL

        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise DataSourceError(f"EONET fetch failed: {e}")

    def parse(self, raw):
        result = []
        fetch_time = datetime.now().isoformat(timespec="seconds")

        # CASE 1: GeoJSON response (bbox)
        if "features" in raw:
            for f in raw.get("features", []):
                props = f.get("properties", {})
                geom = f.get("geometry", {})
                coords = geom.get("coordinates", None)

                title = props.get("title")
                event_id = props.get("id")
                link = props.get("link")
                status = "closed" if props.get("closed") else "open"

                categories = []
                for c in props.get("categories", []):
                    t = c.get("title")
                    if t:
                        categories.append(t)

                lat = None
                lon = None
                g_type = geom.get("type")

                # GeoJSON Point -> [lon, lat]
                if g_type == "Point" and isinstance(coords, list) and len(coords) >= 2:
                    lon, lat = coords[0], coords[1]

                # Keep polygon simple
                result.append(NaturalEvent(
                    type="natural_event",
                    source="NASA EONET",
                    event_id=event_id,
                    title=title,
                    status=status,
                    time=fetch_time,
                    event_time=props.get("date"),
                    categories=categories,
                    link=link,
                    latitude=lat,
                    longitude=lon,
                    geometry_type=g_type
                ))

            return result

        # CASE 2: Normal /events response (no bbox)
        events = raw.get("events", [])
        for ev in events:
            event_id = ev.get("id")
            title = ev.get("title")
            link = ev.get("link")
            status = "closed" if ev.get("closed") else "open"

            categories = [c.get("title") for c in ev.get("categories", []) if c.get("title")]
            geometries = ev.get("geometry", [])

            if not geometries:
                result.append(NaturalEvent(
                    type="natural_event",
                    source="NASA EONET",
                    event_id=event_id,
                    title=title,
                    status=status,
                    time=fetch_time,
                    categories=categories,
                    link=link
                ))
                continue

            for g in geometries:
                g_type = g.get("type")
                coords = g.get("coordinates")
                event_time = g.get("date")

                lat = None
                lon = None
                if g_type == "Point" and isinstance(coords, list) and len(coords) >= 2:
                    lon, lat = coords[0], coords[1]

                result.append(NaturalEvent(
                    type="natural_event",
                    source="NASA EONET",
                    event_id=event_id,
                    title=title,
                    status=status,
                    time=fetch_time,
                    event_time=event_time,
                    categories=categories,
                    link=link,
                    latitude=lat,
                    longitude=lon,
                    geometry_type=g_type
                ))

        return result
