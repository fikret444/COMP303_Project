class CleanedEarthquake:

    def __init__(self, id, event_type, timestamp, magnitude, location, latitude=None, longitude=None):
        self.id = id
        self.event_type = event_type
        self.timestamp = timestamp
        self.location = location
        self.magnitude = magnitude
        self.latitude = latitude
        self.longitude = longitude

    def __repr__(self):
        return f" id:{self.id}, event_type:{self.event_type}, timestamp:{self.timestamp}, location:{self.location}, magnitude:{self.magnitude}"

    def toDictionary(self):
        result = {
            "id": self.id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "magnitude": self.magnitude,
            "location": self.location,
        }
        if self.latitude is not None:
            result["latitude"] = self.latitude
        if self.longitude is not None:
            result["longitude"] = self.longitude
        return result

    @classmethod
    def fromRaw(c, raw_earthquake, id=None):
        if hasattr(raw_earthquake.time, "isoformat"):
            timestamp = raw_earthquake.time.isoformat()
        else:
            timestamp = str(raw_earthquake.time)

        return c(
            id=id if id is not None else 0,
            event_type=raw_earthquake.type,
            timestamp=timestamp,
            location=raw_earthquake.location,
            magnitude=raw_earthquake.magnitude,
            latitude=raw_earthquake.latitude,
            longitude=raw_earthquake.longitude
        )

    def isSignificant(self, t=5.0):
        return self.magnitude > t


class RawEarthquake:

    def __init__(self, type, source, location, magnitude, time, latitude, longitude):
        self.type = type
        self.source = source
        self.location = location
        self.magnitude = magnitude
        self.time = time
        self.latitude = latitude
        self.longitude = longitude

    def __repr__(self):
        return f" type:{self.type}, source:{self.source}, location:{self.location}, magnitude:{self.magnitude}, time:{self.time}, latitude:{self.latitude}, longitude:{self.longitude}"

    def toDictionary(self):
        # Flask/jsonify cannot serialize datetime objects, so convert if needed
        time_val = self.time.isoformat() if hasattr(self.time, "isoformat") else self.time

        return {
            "type": self.type,
            "source": self.source,
            "location": self.location,
            "magnitude": self.magnitude,
            "time": time_val,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }

    @classmethod
    def fromDict(c, data_: dict):
        return c(
            type=data_.get("type"),
            source=data_.get("source"),
            location=data_.get("location"),
            magnitude=data_.get("magnitude"),
            time=data_.get("time"),
            latitude=data_.get("latitude"),
            longitude=data_.get("longitude")
        )

    def isSignificant(self, t=5.0):
        return self.magnitude > t



