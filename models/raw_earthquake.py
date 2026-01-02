class RawEarthquake:

    # 2. class and constructor for earthquake, with parameters in the original dictionary called event

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

    # c = class name (RawEarthquake)
    #this function takes dictionary as argument
    @classmethod
    def fromDict(c, data_:dict):
        return c(
            type=data_.get("type"),
            source=data_.get("source"),
            location=data_.get("location"),
            magnitude=data_.get("magnitude"),
            time=data_.get("time"),
            latitude=data_.get("latitude"),
            longitude=data_.get("longitude")
        )


    #t is treshold
    def isSignificant(self, t = 5.0):
        if self.magnitude > t:
            return True
        else:
            return False