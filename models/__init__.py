"""
Core Data Models
Erdem Kaya - Core System & Data Models
"""

from .raw_earthquake import RawEarthquake
from .cleaned_earthquake import CleanedEarthquake
from .weather import Weather

__all__ = ['RawEarthquake', 'CleanedEarthquake', 'Weather']
