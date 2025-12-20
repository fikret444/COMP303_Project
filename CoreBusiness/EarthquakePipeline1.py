
class EarthquakePipeline1:


    def __init__(self):
        pass


    def generate_and_save(self):

        #earthquake's fetch_events()
        fetch_events()

        #cleanizes raw events then saves (writes) into csv
        save_events_to_csv(clean_earthquake_events(events),filename="earthquakes1Cleaned.csv")

        #saves (writes) raw events into csv
        save_events_to_csv(events,filename="earthquakes2Raw.csv")


        #(earthquake = Earthquake(... , ... , ... , ... , ...) in loop)
        #rows = load_events_from_csv("earthquakes1Cleaned.csv")
        #earthquakesC = [Earthquake(**) for row in rows]


        loaded_clean_earthquakes = load_events_from_csv(filename="earthquakes1Cleaned.csv")

        earthquakesC = []
            for k in loaded_clean_earthquakes:
                earthquake = CleanedEarthquake(
                id = k["id"],
                event_type = k["event_type"],
                timestamp = k["timestamp"],
                magnitude = k["magnitude"],
                location = k["location"]
                )

                earthquakesC.append(earthquake)




        #(earthquake = Earthquake(... , ... , ... , ... , ... , ... , ...) in loop)
        #rows = load_events_from_csv("earthquakes2Raw.csv")
        #earthquakesR = [Earthquake(**) for row in rows]


        loaded_raw_earthquakes = load_events_from_csv(filename="earthquakes2Raw.csv")

        earthquakesR =[]
            for h in loaded_raw_earthquakes:
                earthquake = RawEarthquake(
                type =   h["type"],
                source = h["source"],
                location = h["location"],
                magnitude = h["magnitude"],
                time = h["time"],
                latitude = h["latitude"],
                longitude = h["longitude"]
                )

                earthquakesR.append(earthquake)