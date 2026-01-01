class Weather:

    def __init__(self, type, source, location, temperature, wind_speed, time,
                 humidity=None, pressure=None, wind_direction=None, wind_gust=None,
                 clouds=None, precipitation=None, visibility=None,
                 weather_main=None, weather_description=None, weather_icon=None,
                 sunrise=None, sunset=None, latitude=None, longitude=None,
                 feels_like=None, temp_min=None, temp_max=None, forecast_time=None):
        self.type = type
        self.source = source
        self.location = location
        self.temperature = temperature
        self.wind_speed = wind_speed
        self.time = time
        self.humidity = humidity
        self.pressure = pressure
        self.wind_direction = wind_direction
        self.wind_gust = wind_gust
        self.clouds = clouds
        self.precipitation = precipitation
        self.visibility = visibility
        self.weather_main = weather_main
        self.weather_description = weather_description
        self.weather_icon = weather_icon
        self.sunrise = sunrise
        self.sunset = sunset
        self.latitude = latitude
        self.longitude = longitude
        self.feels_like = feels_like
        self.temp_min = temp_min
        self.temp_max = temp_max
        self.forecast_time = forecast_time  # usually string

    def __repr__(self):
        return f"type:{self.type}, source:{self.source}, location:{self.location}, temperature:{self.temperature}, wind_speed:{self.wind_speed}, time:{self.time}"

    def toDictionary(self):
        # Flask/jsonify cannot serialize datetime objects, so convert if needed
        time_val = self.time.isoformat() if hasattr(self.time, "isoformat") else self.time

        result = {
            "type": self.type,
            "source": self.source,
            "location": self.location,
            "temperature": self.temperature,
            "wind_speed": self.wind_speed,
            "time": time_val,
        }

        if self.humidity is not None:
            result["humidity"] = self.humidity
        if self.pressure is not None:
            result["pressure"] = self.pressure
        if self.wind_direction is not None:
            result["wind_direction"] = self.wind_direction
        if self.wind_gust is not None:
            result["wind_gust"] = self.wind_gust
        if self.clouds is not None:
            result["clouds"] = self.clouds
        if self.precipitation is not None:
            result["precipitation"] = self.precipitation
        if self.visibility is not None:
            result["visibility"] = self.visibility
        if self.weather_main is not None:
            result["weather_main"] = self.weather_main
        if self.weather_description is not None:
            result["weather_description"] = self.weather_description
        if self.weather_icon is not None:
            result["weather_icon"] = self.weather_icon
        if self.sunrise is not None:
            result["sunrise"] = self.sunrise
        if self.sunset is not None:
            result["sunset"] = self.sunset
        if self.latitude is not None:
            result["latitude"] = self.latitude
        if self.longitude is not None:
            result["longitude"] = self.longitude
        if self.feels_like is not None:
            result["feels_like"] = self.feels_like
        if self.temp_min is not None:
            result["temp_min"] = self.temp_min
        if self.temp_max is not None:
            result["temp_max"] = self.temp_max
        if self.forecast_time is not None:
            result["forecast_time"] = self.forecast_time

        return result

    @classmethod
    def fromDict(c, data_: dict):
        return c(
            type=data_.get("type"),
            source=data_.get("source"),
            location=data_.get("location"),
            temperature=data_.get("temperature"),
            wind_speed=data_.get("wind_speed"),
            time=data_.get("time"),
            humidity=data_.get("humidity"),
            pressure=data_.get("pressure"),
            wind_direction=data_.get("wind_direction"),
            wind_gust=data_.get("wind_gust"),
            clouds=data_.get("clouds"),
            precipitation=data_.get("precipitation"),
            visibility=data_.get("visibility"),
            weather_main=data_.get("weather_main"),
            weather_description=data_.get("weather_description"),
            weather_icon=data_.get("weather_icon"),
            sunrise=data_.get("sunrise"),
            sunset=data_.get("sunset"),
            latitude=data_.get("latitude"),
            longitude=data_.get("longitude"),
            feels_like=data_.get("feels_like"),
            temp_min=data_.get("temp_min"),
            temp_max=data_.get("temp_max"),
            forecast_time=data_.get("forecast_time")
        )
