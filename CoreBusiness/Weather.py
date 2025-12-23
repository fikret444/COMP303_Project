class Weather:

    def __init__(self, type, source, location, temperature, wind_speed, time):
        self.type = type
        self.source = source
        self.location = location
        self.temperature = temperature
        self.wind_speed = wind_speed
        self.time = time


    def __repr__(self):
        return f"type:{self.type}, source:{self.source}, location:{self.location}, temperature:{self.temperature}, wind_speed:{self.wind_speed}, time:{self.time}"

    def toDictionary(self):
        return {

            "type": self.type,
            "source": self.source,
            "location": self.location,
            "temperature": self.temperature,
            "wind_speed": self.wind_speed,
            "time": self.time,
        }

    # c = class name (Weather)
    #this function takes dictionary as argument
    @classmethod
    def fromDict(c, data_:dict):
        return c(
            type=data_["type"],
            source=data_["source"],
            location=data_["location"],
            temperature=data_["temperature"],
            wind_speed=data_["wind_speed"],
            time=data_["time"]
        )

