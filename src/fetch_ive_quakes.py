from datasources.usgs_earthquake import USGSEarthquakeSource
from src.processing import clean_earthquake_events
from src.storage import save_events_to_csv, log_message

def adapt_usgs_events(usgs_events):
    