class NaturalEvent:

    def __init__(self, type, source, event_id, title, status, time,
                 event_time=None, categories=None, link=None,
                 latitude=None, longitude=None, geometry_type=None):
        self.type = type
        self.source = source
        self.event_id = event_id
        self.title = title
        self.status = status
        self.time = time
        self.event_time = event_time
        self.categories = categories or []
        self.link = link
        self.latitude = latitude
        self.longitude = longitude
        self.geometry_type = geometry_type

    def __repr__(self):
        return f"type:{self.type}, source:{self.source}, title:{self.title}, status:{self.status}, event_time:{self.event_time}"

    def toDictionary(self):
        result = {
            "type": self.type,
            "source": self.source,
            "event_id": self.event_id,
            "title": self.title,
            "status": self.status,
            "time": self.time
        }

        if self.event_time is not None:
            result["event_time"] = self.event_time
        if self.categories:
            result["categories"] = self.categories
        if self.link is not None:
            result["link"] = self.link
        if self.latitude is not None:
            result["latitude"] = self.latitude
        if self.longitude is not None:
            result["longitude"] = self.longitude
        if self.geometry_type is not None:
            result["geometry_type"] = self.geometry_type

        return result

    @classmethod
    def fromDict(c, data_: dict):
        return c(
            type=data_.get("type"),
            source=data_.get("source"),
            event_id=data_.get("event_id"),
            title=data_.get("title"),
            status=data_.get("status"),
            time=data_.get("time"),
            event_time=data_.get("event_time"),
            categories=data_.get("categories") or [],
            link=data_.get("link"),
            latitude=data_.get("latitude"),
            longitude=data_.get("longitude"),
            geometry_type=data_.get("geometry_type")
        )
