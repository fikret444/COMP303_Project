import traceback
from datasources.usgs_earthquake import USGSEarthquakeSource
from datasources.openweather_source import OpenWeatherSource, AMERICAS_CITY_COUNTRY_MAP
from datasources.eonet_source import EONETSource
from datasources.eonet_wildfire_source import EONETWildfireSource
from datasources.eonet_storm_source import EONETStormSource
from datasources.eonet_volcano_source import EONETVolcanoSource
from datasources.flood_openmeteo_source import OpenMeteoFloodSource
from pipeline import RuntimeSystem
from pipeline.fetch_flood import CITIES as FLOOD_CITIES
from processing import log_message


def main():

    americas_bbox = [-180, -60, -30, 85]
    earthquake_source = USGSEarthquakeSource(bbox=americas_bbox)
    log_message("Earthquakes are ready (America)", "INFO")

    weather_sources = [
        OpenWeatherSource(city=city, include_forecast=True)
        for city in AMERICAS_CITY_COUNTRY_MAP.keys()
    ]
    log_message(f"{len(weather_sources)} Weather is ready (America)", "INFO")

    eonet_source = EONETSource(status="open", days=30, limit=100, bbox=americas_bbox)
    log_message("EONET Source is ready (America)", "INFO")
    
    wildfire_source = EONETWildfireSource(days=90, status="all")
    log_message("EONET Wildfire Source is ready (America)", "INFO")

    storm_source = EONETStormSource(days=60, status="all")
    log_message("EONET Storm Source is ready (America)", "INFO")
    
    volcano_source = EONETVolcanoSource(days=90, status="all")
    log_message("EONET Volcano Source is ready (America)", "INFO")
    
    flood_sources = [
        OpenMeteoFloodSource(latitude=lat, longitude=lon, location_name=city, past_days=3, forecast_days=7)
        for city, lat, lon in FLOOD_CITIES
    ]
    log_message(f" {len(flood_sources)} OpenMeteo Flood Source is ready", "INFO")

    log_message("Creating runtime system...", "INFO")
    
    all_sources = [
        earthquake_source,
        eonet_source,
        wildfire_source,
        storm_source,
        volcano_source
    ]
    all_sources.extend(weather_sources)
    all_sources.extend(flood_sources)
    
    runtime = RuntimeSystem(
        data_sources=all_sources,
    )
    
    log_message("Runtime system is ready", "INFO")
    
    try:
        runtime.start()
        
    except KeyboardInterrupt:
        log_message("\nDetected keyboard interrupt", "INFO")
    except Exception as e:
        log_message(f"Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
    finally:
        runtime.stop()
        log_message("System stopped", "INFO")


if __name__ == "__main__":
    main()
