class CleanedEarthquake:


    # 1. class and constructor for earthquake, with cleaned version of data

    def __init__(self, id, event_type, timestamp, magnitude, location):
        self.id = id
        self.event_type = event_type
        self.timestamp = timestamp
        self.location = location
        self.magnitude = magnitude

    def __repr__(self):
        return f" id:{self.id}, event_type:{self.event_type}, timestamp:{self.timestamp}, location:{self.location}, magnitude:{self.magnitude}"



    def toDictionary(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "magnitude": self.magnitude,
            "location": self.location,
        }


    #c = class name(CleanedEarthquake)
    #this function takes object as argument
    @classmethod
    def fromRaw(c, raw_earthquake):
        return c(
            id=raw_earthquake.id,
            event_type=raw_earthquake.type,
            timestamp=raw_earthquake.time,
            location=raw_earthquake.location,
            magnitude=raw_earthquake.magnitude
        )


    #t is treshold
    def isSignificant(self, t = 5.0):
        if self.magnitude > t:
            return True
        else:
            return False










