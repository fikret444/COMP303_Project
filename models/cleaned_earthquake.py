class CleanedEarthquake:


    # 1. class and constructor for earthquake, with cleaned version of data

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
        # Add optional latitude/longitude if they exist
        if self.latitude is not None:
            result["latitude"] = self.latitude
        if self.longitude is not None:
            result["longitude"] = self.longitude
        return result


    #c = class name(CleanedEarthquake)
    #this function takes object as argument
    @classmethod
    def fromRaw(c, raw_earthquake, id=None):
        """
        Create CleanedEarthquake from RawEarthquake object.
        id parameter is optional - if not provided, will be None.
        """
        # Convert time to ISO string if it's a datetime object
        if hasattr(raw_earthquake.time, "isoformat"):
            timestamp = raw_earthquake.time.isoformat()
        else:
            timestamp = str(raw_earthquake.time)
            
        return c(
            id=id if id is not None else 0,  # Default to 0 if not provided
            event_type=raw_earthquake.type,
            timestamp=timestamp,
            location=raw_earthquake.location,
            magnitude=raw_earthquake.magnitude,
            latitude=raw_earthquake.latitude,
            longitude=raw_earthquake.longitude
        )


    #t is treshold
    def isSignificant(self, t = 5.0):
        if self.magnitude > t:
            return True
        else:
            return False










