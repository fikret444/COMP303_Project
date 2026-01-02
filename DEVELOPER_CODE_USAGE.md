# Geliştirici Kod Kullanım Raporu

Bu dokümanda her geliştiricinin yazdığı kodların projede nerede kullanıldığı detaylı olarak gösterilmektedir.

---

## 1. HAKAN DEMİRCAN - API Integration & Web Scraping

### Dosyaları:
- `datasources/usgs_earthquake.py` - USGS deprem API'si
- `datasources/openweather_source.py` - OpenWeather hava durumu API'si
- `datasources/eonet_source.py` - NASA EONET genel API'si
- `datasources/eonet_wildfire_source.py` - EONET yangın verileri
- `datasources/eonet_storm_source.py` - EONET fırtına verileri
- `datasources/eonet_volcano_source.py` - EONET volkan verileri
- `datasources/flood_openmeteo_source.py` - OpenMeteo sel verileri
- `datasources/base_source.py` - Tüm data source'ların base class'ı
- `datasources/scraping/scrape_news.py` - Haber scraping modülü

### Kullanım Yerleri:

#### 1.1 `main_runtime.py` (Ana Runtime Sistemi)
```python
# Satır 18-24: Tüm Hakan'ın data source'ları import ediliyor
from datasources.usgs_earthquake import USGSEarthquakeSource
from datasources.openweather_source import OpenWeatherSource
from datasources.eonet_source import EONETSource
from datasources.eonet_wildfire_source import EONETWildfireSource
from datasources.eonet_storm_source import EONETStormSource
from datasources.eonet_volcano_source import EONETVolcanoSource
from datasources.flood_openmeteo_source import OpenMeteoFloodSource

# Satır 62: USGS Earthquake Source kullanılıyor
earthquake_source = USGSEarthquakeSource(bbox=americas_bbox)

# Satır 69-94: 20 farklı şehir için OpenWeather Source'ları oluşturuluyor
weather_sources = [
    OpenWeatherSource(city="New York", country_code="US", include_forecast=True),
    # ... 19 şehir daha
]

# Satır 102: EONET Source kullanılıyor
eonet_source = EONETSource(status="open", days=30, limit=100, bbox=americas_bbox)

# Satır 110: EONET Wildfire Source kullanılıyor
wildfire_source = EONETWildfireSource(days=90, status="all", bbox=americas_bbox_str)

# Satır 115: EONET Storm Source kullanılıyor
storm_source = EONETStormSource(days=60, status="all", bbox=americas_bbox_str)

# Satır 120: EONET Volcano Source kullanılıyor
volcano_source = EONETVolcanoSource(days=90, status="all", bbox=americas_bbox_str)

# Satır 137-140: 10 şehir için OpenMeteo Flood Source'ları oluşturuluyor
flood_sources = [
    OpenMeteoFloodSource(latitude=lat, longitude=lon, location_name=city, ...)
    for city, lat, lon in flood_cities
]

# Satır 147: Tüm source'lar birleştiriliyor
all_sources = [earthquake_source] + weather_sources + [eonet_source] + ...
```

#### 1.2 `dashboard.py` (Web Dashboard)
```python
# Satır 16: News scraping modülü import ediliyor
from datasources.scraping.scrape_news import scrape_all_risk_headlines

# Satır 25: EONET Source import ediliyor
from datasources.eonet_source import EONETSource

# Satır 272: News scraping kullanılıyor
news = scrape_all_risk_headlines()
```

#### 1.3 `pipeline/event_pipeline.py` (Event Processing)
```python
# Satır 37-43: Her data source için processor tanımlanıyor
self.processors = {
    'USGSEarthquakeSource': self._process_earthquake_events,
    'OpenWeatherSource': self._process_weather_events,
    'EONETSource': self._process_eonet_events,
    'EONETWildfireSource': self._process_wildfire_events,
    'EONETStormSource': self._process_storm_events,
    'EONETVolcanoSource': self._process_volcano_events,
    'OpenMeteoFloodSource': self._process_flood_events,
    ...
}
```

#### 1.4 `pipeline/fetch_wildfires.py` (Yangın Verisi İşleme)
```python
# Satır 11: EONET Wildfire Source import ediliyor
from datasources.eonet_wildfire_source import EONETWildfireSource

# Satır 51-52: Source kullanılarak veri çekiliyor
raw = src.fetch_raw()
events = src.parse(raw)
```

#### 1.5 `pipeline/fetch_storms.py` (Fırtına Verisi İşleme)
```python
# Satır 11: EONET Storm Source import ediliyor
from datasources.eonet_storm_source import EONETStormSource

# Satır 181-182: Source kullanılarak veri çekiliyor
raw = src.fetch_raw()
events = src.parse(raw)
```

#### 1.6 `pipeline/fetch_flood.py` (Sel Verisi İşleme)
```python
# Satır 10: OpenMeteo Flood Source import ediliyor
from datasources.flood_openmeteo_source import OpenMeteoFloodSource

# Satır 51-52: Source kullanılarak veri çekiliyor
raw = src.fetch_raw()
events = src.parse(raw)
```

#### 1.7 `pipeline/data_source_manager.py` (Data Source Yönetimi)
```python
# Satır 12: Base Source import ediliyor
from datasources.base_source import DataSource

# Tüm Hakan'ın source'ları DataSourceManager tarafından yönetiliyor
```

#### 1.8 `datasources/openweather_source.py` ve `usgs_earthquake.py`
```python
# Bu dosyalar içinde Erdem'in modelleri kullanılıyor:
from models import Weather  # openweather_source.py
from models import RawEarthquake  # usgs_earthquake.py
```

---

## 2. ERDEM KAYA - Core System & Data Models

### Dosyaları:
- `models/raw_earthquake.py` - Ham deprem verisi modeli
- `models/cleaned_earthquake.py` - Temizlenmiş deprem verisi modeli
- `models/earthquake.py` - Deprem modeli (RawEarthquake, CleanedEarthquake export)
- `models/weather.py` - Hava durumu modeli
- `models/natural_event.py` - Doğal afet event modeli
- `models/__init__.py` - Model export'ları

### Kullanım Yerleri:

#### 2.1 `datasources/usgs_earthquake.py` (Hakan'ın Kodu)
```python
# Satır 4: RawEarthquake modeli import ediliyor
from models import RawEarthquake

# Satır 40-50: USGS verileri RawEarthquake objelerine dönüştürülüyor
return RawEarthquake(
    id=usgs_id,
    magnitude=mag,
    location={"latitude": lat, "longitude": lon},
    timestamp=dt,
    ...
)
```

#### 2.2 `datasources/openweather_source.py` (Hakan'ın Kodu)
```python
# Satır 6: Weather modeli import ediliyor
from models import Weather

# Satır 60-80: OpenWeather verileri Weather objelerine dönüştürülüyor
return Weather(
    city=city,
    country=country,
    temperature=temp,
    ...
)
```

#### 2.3 `processing/earthquake_processing.py` (Efe'nin Kodu)
```python
# Satır 3: Deprem modelleri import ediliyor
from models import RawEarthquake, CleanedEarthquake

# Satır 50-100: RawEarthquake objeleri CleanedEarthquake'e dönüştürülüyor
def clean_usgs_earthquake_events(raw_events):
    cleaned = []
    for raw in raw_events:
        if isinstance(raw, RawEarthquake):
            cleaned.append(CleanedEarthquake(...))
    return cleaned
```

#### 2.4 `pipeline/event_pipeline.py` (Fikret'in Kodu)
```python
# Satır 91: Weather modeli import ediliyor
from models import Weather

# Satır 49-79: RawEarthquake objeleri işleniyor
def _process_earthquake_events(self, events, source_name):
    cleaned_events = clean_usgs_earthquake_events(events)  # CleanedEarthquake döner
    ...
```

#### 2.5 `models/__init__.py` (Model Export'ları)
```python
# Tüm modeller buradan export ediliyor:
from .weather import Weather
from .earthquake import RawEarthquake, CleanedEarthquake
from .natural_event import NaturalEvent
```

---

## 3. YAĞIZ EFE HÜŞAN - Data Processing & Analytics

### Dosyaları:
- `processing/storage.py` - Veri saklama ve loglama
- `processing/earthquake_processing.py` - Veri temizleme ve dönüştürme
- `processing/analytics.py` - Veri analizi ve istatistikler
- `pipeline/fetch_wildfires.py` - Yangın verisi işleme
- `pipeline/fetch_storms.py` - Fırtına verisi işleme
- `pipeline/fetch_flood.py` - Sel verisi işleme
- `datasources/eonet_wildfire_source.py` - EONET yangın source'u
- `datasources/eonet_storm_source.py` - EONET fırtına source'u
- `datasources/flood_openmeteo_source.py` - OpenMeteo sel source'u
- `datasources/eonet_volcano_source.py` - EONET volkan source'u

### Kullanım Yerleri:

#### 3.1 `main_runtime.py` (Ana Runtime)
```python
# Satır 26: Storage modülünden log_message import ediliyor
from processing import log_message

# Satır 48, 56, 63, 95, 103, 111, 116, 121, 141, 144, 155, 161, 164, 171, 178:
# log_message fonksiyonu tüm sistem boyunca kullanılıyor
log_message("SDEWS System Initialization", "INFO")
log_message("Data source'lar baslatiliyor...", "INFO")
# ... ve daha fazlası
```

#### 3.2 `pipeline/event_pipeline.py` (Event Processing)
```python
# Satır 12-17: Processing modülleri import ediliyor
from processing import (
    log_message,
    clean_usgs_earthquake_events,  # Efe'nin earthquake_processing.py'den
    save_events_to_json,  # Efe'nin storage.py'den
    compute_basic_stats  # Efe'nin analytics.py'den
)

# Satır 53: clean_usgs_earthquake_events kullanılıyor
cleaned_events = clean_usgs_earthquake_events(events)

# Satır 57: save_events_to_json kullanılıyor
save_events_to_json(cleaned_events, filename)

# Satır 60-61: cleanup_old_files kullanılıyor
from processing.storage import cleanup_old_files
cleanup_old_files()

# Satır 65: compute_basic_stats kullanılıyor
stats = compute_basic_stats(stats_events)

# Satır 90: DATA_DIR kullanılıyor
from processing.storage import DATA_DIR

# Satır 152: cleanup_old_files tekrar kullanılıyor
from processing.storage import cleanup_old_files

# Satır 214: fetch_wildfires modülünden assign_city kullanılıyor
from pipeline.fetch_wildfires import assign_city

# Satır 245: fetch_storms modülünden assign_city kullanılıyor
from pipeline.fetch_storms import assign_city

# Satır 304: DATA_DIR tekrar kullanılıyor
from processing.storage import DATA_DIR
```

#### 3.3 `dashboard.py` (Web Dashboard)
```python
# Satır 12: cleanup_old_files import ediliyor
from processing.storage import cleanup_old_files

# Satır 1233: cleanup_old_files kullanılıyor (main block'ta)
if __name__ == '__main__':
    cleanup_old_files()
    app.run(debug=True, host='0.0.0.0', port=5000)
```

#### 3.4 `pipeline/fetch_wildfires.py` (Efe'nin Kendi Dosyası)
```python
# Satır 11-12: Kendi modüllerini kullanıyor
from datasources.eonet_wildfire_source import EONETWildfireSource
from processing.storage import log_message

# Satır 51-52: Source'dan veri çekiyor
raw = src.fetch_raw()
events = src.parse(raw)

# Satır 175-200: assign_city fonksiyonu tanımlanıyor (event_pipeline.py tarafından kullanılıyor)
def assign_city(lat, lon):
    # Şehir atama mantığı
    ...
```

#### 3.5 `pipeline/fetch_storms.py` (Efe'nin Kendi Dosyası)
```python
# Satır 11-12: Kendi modüllerini kullanıyor
from datasources.eonet_storm_source import EONETStormSource
from processing.storage import log_message

# Satır 181-182: Source'dan veri çekiyor
raw = src.fetch_raw()
events = src.parse(raw)

# Satır 200-225: assign_city fonksiyonu tanımlanıyor (event_pipeline.py tarafından kullanılıyor)
def assign_city(lat, lon):
    # Şehir atama mantığı
    ...
```

#### 3.6 `pipeline/fetch_flood.py` (Efe'nin Kendi Dosyası)
```python
# Satır 10-11: Kendi modüllerini kullanıyor
from datasources.flood_openmeteo_source import OpenMeteoFloodSource
from processing.storage import log_message

# Satır 51-52: Source'dan veri çekiyor
raw = src.fetch_raw()
events = src.parse(raw)
```

#### 3.7 `processing/earthquake_processing.py` (Efe'nin Kendi Dosyası)
```python
# Satır 2: Kendi storage modülünü kullanıyor
from .storage import log_message

# Satır 3: Erdem'in modellerini kullanıyor
from models import RawEarthquake, CleanedEarthquake

# Satır 50-100: clean_usgs_earthquake_events fonksiyonu
# event_pipeline.py tarafından kullanılıyor
def clean_usgs_earthquake_events(raw_events):
    ...
```

#### 3.8 `processing/storage.py` (Efe'nin Kendi Dosyası)
```python
# Bu dosya tüm projede kullanılıyor:
# - log_message() fonksiyonu
# - save_events_to_json() fonksiyonu
# - cleanup_old_files() fonksiyonu
# - DATA_DIR constant'ı
```

#### 3.9 `processing/analytics.py` (Efe'nin Kendi Dosyası)
```python
# compute_basic_stats fonksiyonu event_pipeline.py tarafından kullanılıyor
def compute_basic_stats(events):
    # İstatistik hesaplamaları
    ...
```

---

## 4. FİKRET AHISKALI - Concurrency & Runtime Pipeline

### Dosyaları:
- `pipeline/runtime_system.py` - Ana runtime sistemi
- `pipeline/data_source_manager.py` - Data source yönetimi (concurrent fetching)
- `pipeline/event_pipeline.py` - Event processing pipeline (Producer-Consumer pattern)
- `main_runtime.py` - Ana entry point (tüm sistemi birleştiriyor)

### Kullanım Yerleri:

#### 4.1 `main_runtime.py` (Fikret'in Kendi Dosyası)
```python
# Satır 25: Kendi RuntimeSystem'ini import ediyor
from pipeline import RuntimeSystem

# Satır 149-153: RuntimeSystem oluşturuluyor
runtime = RuntimeSystem(
    data_sources=all_sources,  # Hakan'ın source'ları
    fetch_interval=120,
    num_consumers=5
)

# Satır 168: Runtime sistemi başlatılıyor
runtime.start(continuous=continuous)

# Satır 178: Runtime sistemi durduruluyor
runtime.stop()
```

#### 4.2 `pipeline/runtime_system.py` (Fikret'in Kendi Dosyası)
```python
# Satır 13-14: Kendi modüllerini kullanıyor
from .data_source_manager import DataSourceManager
from .event_pipeline import EventPipeline

# Satır 12: Hakan'ın base_source'unu kullanıyor
from datasources.base_source import DataSource

# RuntimeSystem, DataSourceManager ve EventPipeline'ı koordine ediyor
```

#### 4.3 `pipeline/data_source_manager.py` (Fikret'in Kendi Dosyası)
```python
# Satır 12: Hakan'ın base_source'unu kullanıyor
from datasources.base_source import DataSource

# DataSourceManager, tüm Hakan'ın source'larını concurrent olarak yönetiyor
# Threading kullanarak paralel veri çekme işlemi yapıyor
```

#### 4.4 `pipeline/event_pipeline.py` (Fikret'in Kendi Dosyası)
```python
# Satır 12-17: Efe'nin processing modüllerini kullanıyor
from processing import (
    log_message,
    clean_usgs_earthquake_events,
    save_events_to_json,
    compute_basic_stats
)

# Satır 91: Erdem'in Weather modelini kullanıyor
from models import Weather

# Satır 214: Efe'nin fetch_wildfires modülünü kullanıyor
from pipeline.fetch_wildfires import assign_city

# Satır 245: Efe'nin fetch_storms modülünü kullanıyor
from pipeline.fetch_storms import assign_city

# EventPipeline, Producer-Consumer pattern ile event'leri işliyor
# Her data source tipi için özel processor fonksiyonları var
```

#### 4.5 `pipeline/__init__.py` (Fikret'in Export Dosyası)
```python
# Satır 6-8: Tüm pipeline modülleri export ediliyor
from .data_source_manager import DataSourceManager
from .event_pipeline import EventPipeline
from .runtime_system import RuntimeSystem
```

#### 4.6 `test_runtime.py` (Test Dosyası)
```python
# Satır 11: Fikret'in pipeline modüllerini test ediyor
from pipeline import DataSourceManager, EventPipeline, RuntimeSystem
```

---

## ÖZET: Kod Bağımlılıkları

### Hakan'ın Kodları:
- ✅ **Kullanılıyor**: Tüm data source'lar (`main_runtime.py`, `dashboard.py`, `pipeline/` modülleri)
- ✅ **Bağımlılık**: Erdem'in `models/` modüllerini kullanıyor
- ✅ **Kullanıcılar**: Fikret (pipeline), Efe (fetch modülleri), Dashboard

### Erdem'in Kodları:
- ✅ **Kullanılıyor**: Tüm model sınıfları (`datasources/`, `processing/`, `pipeline/`)
- ✅ **Bağımlılık**: Yok (base modeller)
- ✅ **Kullanıcılar**: Hakan (data source'lar), Efe (data processing), Fikret (event pipeline)

### Efe'nin Kodları:
- ✅ **Kullanılıyor**: Tüm processing modülleri (`pipeline/event_pipeline.py`, `dashboard.py`)
- ✅ **Bağımlılık**: Erdem'in `models/` modüllerini kullanıyor
- ✅ **Kullanıcılar**: Fikret (event pipeline), Dashboard

### Fikret'in Kodları:
- ✅ **Kullanılıyor**: Ana runtime sistemi (`main_runtime.py`)
- ✅ **Bağımlılık**: Hakan'ın `datasources/`, Efe'nin `processing/`, Erdem'in `models/`
- ✅ **Kullanıcılar**: Ana sistem entry point

---

## SONUÇ

**Tüm geliştiricilerin kodları aktif olarak kullanılıyor!**

- **Hakan**: API entegrasyonları ve data source'lar → Ana runtime ve dashboard'da kullanılıyor
- **Erdem**: Data modelleri → Tüm sistemde kullanılıyor (Hakan, Efe, Fikret)
- **Efe**: Data processing ve analytics → Pipeline ve dashboard'da kullanılıyor
- **Fikret**: Runtime pipeline ve concurrency → Ana sistem koordinasyonu

Herkesin branch'inden çekilen kodlar entegre edilmiş ve aktif olarak çalışıyor! 🎉

