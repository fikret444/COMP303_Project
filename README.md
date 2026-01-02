# SDEWS - Smart Disaster Early Warning System

## Project Overview

SDEWS is a Python-based disaster early warning system that collects, processes, and analyzes real-time data from multiple sources including earthquakes, weather, wildfires, storms, volcanoes, and floods. The system features concurrent data fetching, multi-threaded processing, and a web-based visualization dashboard.

## Team & Responsibilities

| Member | Role | Responsibilities |
|--------|------|------------------|
| **Hakan Demircan** | API Integration & Web Scraping | `datasources/` - USGS, OpenWeather, EONET APIs, News scraping |
| **Erdem Kaya** | Core System & Data Models | `models/` - RawEarthquake, CleanedEarthquake, Weather, NaturalEvent |
| **Yağız Efe Hüşan** | Data Processing & Analytics | `processing/` - Storage, data cleaning, analytics, earthquake processing, flood analysis |
| **Fikret Ahıskalı** | Concurrency, Runtime Pipeline & Dashboard | `pipeline/`, `dashboard.py`, `templates/` - Threading, queues, orchestration, web dashboard, seismic simulation |

## System Architecture

The system uses a Producer-Consumer pattern with multi-threaded data fetching and processing:

```
RuntimeSystem (Main Orchestrator)
    ├── DataSourceManager (Producer)
    │   ├── USGSEarthquakeSource (Americas)
    │   ├── OpenWeatherSource (20+ cities in Americas)
    │   ├── EONETWildfireSource
    │   ├── EONETStormSource
    │   ├── EONETVolcanoSource
    │   └── OpenMeteoFloodSource (10+ cities)
    │
    └── EventPipeline (Consumer)
        ├── Data Cleaning (Efe)
        ├── Analytics (Efe)
        └── Storage (Efe)
```

## Project Structure

```
COMP303_Project/
├── datasources/          # Hakan - API & Web Scraping
│   ├── usgs_earthquake.py
│   ├── openweather_source.py
│   ├── eonet_source.py
│   ├── eonet_wildfire_source.py
│   ├── eonet_storm_source.py
│   ├── eonet_volcano_source.py
│   ├── flood_openmeteo_source.py
│   └── scraping/
│       └── scrape_news.py
├── models/               # Erdem - Core Data Models
│   ├── raw_earthquake.py
│   ├── cleaned_earthquake.py
│   ├── weather.py
│   └── natural_event.py
├── processing/           # Efe - Data Processing
│   ├── storage.py
│   ├── earthquake_processing.py
│   ├── flood_regional_analysis.py
│   ├── analytics.py
│   ├── seismic_risk_analyzer.py
│   └── seismic_simulation.py
├── pipeline/             # Fikret - Concurrency & Pipeline
│   ├── data_source_manager.py
│   ├── event_pipeline.py
│   ├── runtime_system.py
│   ├── fetch_wildfires.py
│   ├── fetch_storms.py
│   ├── fetch_volcanoes.py
│   └── fetch_flood.py
├── templates/            # Fikret - Web Dashboard Frontend
│   └── dashboard.html
├── dashboard.py          # Fikret - Flask Web Dashboard & API
├── main_runtime.py       # Fikret - Main Runtime Entry Point
├── data/                 # Processed data (JSON)
├── logs/                 # System logs
├── config.py             # API keys and settings
└── requirements.txt       # Python dependencies
```

## Installation

### Requirements

- Python 3.9 or higher (required for zoneinfo module)
- OpenWeather API key (optional, for weather data)
- USGS API key not required (free public API)
- NASA EONET API (free, no key required)

### Steps

1. Clone or download the project
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Configure API keys:
   - Edit `config.py` file or
   - Set as environment variable:
     ```bash
     set OPENWEATHER_API_KEY=your_api_key_here
     ```

## Usage

### Data Collection System

#### Continuous Mode
```bash
python main_runtime.py
```
- Fetches data every 2 minutes
- Runs until stopped with Ctrl+C
- Saves data to `data/` directory

#### Single Run Mode
```bash
python main_runtime.py --once
```
- Fetches data once and exits
- Ideal for testing

### Web Dashboard

#### Starting the Dashboard
```bash
python dashboard.py
```

Open in browser:
```
http://localhost:5000
```

#### Dashboard Features

- **Interactive Map**: Real-time visualization of all disaster events
  - Earthquakes (USGS)
  - Weather conditions (OpenWeather)
  - Wildfires (NASA EONET)
  - Storms (NASA EONET)
  - Volcanoes (NASA EONET)
  - Flood risks (OpenMeteo)
  - Seismic risk analysis
  - Earthquake swarms
  - Seismic sensors (24 sensors across Americas)

- **Event Lists**: Filterable sidebar with all events
- **Weather Window**: Current conditions and forecasts
- **Seismic Risk Analysis**: Fault line analysis and earthquake swarm detection
- **Earthquake Simulation**: Interactive early warning system simulation

#### API Endpoints

**Data Endpoints:**
- `GET /` - Dashboard main page
- `GET /api/earthquakes` - Earthquake data and statistics
- `GET /api/weather` - Current weather data
- `GET /api/forecast` - 5-day weather forecasts
- `GET /api/forecast/<city>` - Forecast for specific city
- `GET /api/wildfires` - Wildfire events
- `GET /api/storms` - Storm events
- `GET /api/volcanoes` - Volcano events
- `GET /api/floods` - Flood risk data

**Alert Endpoints:**
- `GET /api/alerts` - All alerts (current + forecast)
- `GET /api/alerts/current` - Current condition alerts
- `GET /api/alerts/forecast` - Forecast-based alerts
- `GET /api/news` - Risk-related news headlines

**Seismic Analysis Endpoints:**
- `GET /api/seismic-risk/faults` - List of fault lines
- `GET /api/seismic-risk/fault/<fault_id>` - Analyze specific fault
- `GET /api/seismic-risk/region` - Regional seismic risk analysis
- `GET /api/seismic-risk/swarms` - Earthquake swarm detection

**Simulation Endpoints:**
- `POST /api/seismic-simulation/trigger` - Trigger earthquake simulation

**Utility Endpoints:**
- `GET /api/all` - All data (earthquakes + weather + forecasts)

## Features

### Data Sources (Hakan)

- **USGS Earthquake API**: Last 24 hours of earthquake data (Americas only)
- **OpenWeather API**: 
  - Current weather (20+ cities in Americas)
  - 5-day forecasts (3-hour intervals)
- **NASA EONET API**:
  - Wildfires (last 90 days)
  - Severe storms (last 60 days)
  - Volcanoes (last 90 days)
- **OpenMeteo API**: Flood risk data for 10+ cities
- **Web Scraping**: Risk-related news headlines from news websites

### Data Processing (Efe)

- **Earthquake Processing** (`earthquake_processing.py`):
  - USGS data cleaning and normalization
  - RawEarthquake to CleanedEarthquake conversion
  - Data validation and error handling

- **Flood Regional Analysis** (`flood_regional_analysis.py`):
  - Regional flood risk analysis
  - City-based risk statistics
  - Risk level categorization (high, medium, low)

- **Storage & Analytics**:
  - JSON format storage
  - Statistical analysis (average, min, max magnitude)
  - Event filtering (magnitude, region, time)
  - Automatic file cleanup

### Seismic Risk Analysis

- **Seismic Gap Theory**: Analysis based on historical earthquake patterns
- **Fault Line Analysis**: Risk assessment for predefined fault lines
- **Regional Analysis**: Custom region-based risk evaluation
- **Earthquake Swarm Detection**: Identifies clusters of small earthquakes

### Seismic Simulation

- **Early Warning System**: Simulates earthquake detection and early warning
- **24 Sensor Network**: Distributed sensors across Americas
- **Wave Propagation**: P-wave and S-wave arrival time calculations
- **Interactive Map Selection**: Users can select epicenter location via map click

### Concurrency & Runtime Pipeline (Fikret)

- **RuntimeSystem**: Ana orkestratör, sistem başlatma/durdurma, iki çalışma modu (continuous/once)
- **DataSourceManager**: 35+ veri kaynağını paralel çekme, thread-safe queue yönetimi
- **EventPipeline**: Producer-Consumer pattern, 5 paralel consumer thread, event işleme
- Multi-threaded data fetching
- Thread-safe queue communication
- Lock-based synchronization
- Optimize edilmiş timeout yönetimi
- Graceful shutdown ve signal handling

### Web Dashboard (Fikret)

- **Flask Framework**: RESTful API, 20+ endpoint
- **Interactive Map**: Leaflet.js ile gerçek zamanlı görselleştirme
- **Filtering System**: Kategori bazlı filtreleme
- **Event Lists**: Sidebar'da tüm event'lerin listelenmesi
- **Weather Window**: Hava durumu penceresi
- **Responsive Design**: Mobil uyumlu tasarım

### Seismic Simulation (Fikret)

- **Early Warning System**: Deprem erken uyarı sistemi simülasyonu
- **24 Sensor Network**: Amerika kıtalarında dağıtılmış sensör ağı
- **Wave Propagation**: P-dalga (6 km/s) ve S-dalga (3.5 km/s) hesaplamaları
- **Interactive Map Selection**: Kullanıcı haritada tıklayarak deprem merkez üssü seçebilir
- **Real-time Countdown**: Gerçek zamanlı geri sayım timer'ı
- **Critical Actions**: Büyüklüğe göre kritik güvenlik protokolleri

### Data Models (Erdem)

- **RawEarthquake**: Raw earthquake data model
- **CleanedEarthquake**: Cleaned earthquake data model
- **Weather**: Weather data model
- **NaturalEvent**: Generic natural event model
- Data validation and type checking

### Alert System

The system automatically generates alerts:

**Current Condition Alerts:**
- Earthquakes: Magnitude >= 5.0
- Weather:
  - Extreme heat (>= 35°C)
  - Extreme cold (<= -5°C)
  - High wind (>= 15 m/s)
  - High humidity (>= 90%)
  - Low pressure (<= 1000 hPa)
  - Low visibility (<= 1000m)
  - Precipitation, snow, heavy cloud cover

**Forecast-Based Alerts:**
- Low/high temperature predictions
- High wind predictions
- Snow predictions
- Precipitation predictions
- Low pressure predictions

## Data Formats

### Earthquake Data (earthquakes_*.json)
```json
{
  "id": 1,
  "event_type": "earthquake",
  "timestamp": "2025-12-21T00:23:42.890000",
  "location": "8 km SW of Guánica, Puerto Rico",
  "magnitude": 2.47,
  "latitude": 17.9195,
  "longitude": -66.9663
}
```

### Weather Data (weather_all.json)
```json
{
  "type": "weather",
  "source": "OpenWeatherMap",
  "location": "New York",
  "temperature": 10.09,
  "feels_like": 8.5,
  "humidity": 87,
  "pressure": 1013,
  "wind_speed": 4.12,
  "wind_direction": 270,
  "clouds": 75,
  "precipitation": 0,
  "visibility": 10000,
  "latitude": 40.7128,
  "longitude": -74.0060,
  "time": "2025-12-23T11:32:11"
}
```

### Natural Event Data (wildfires.json, storms.json, volcanoes.json)
```json
{
  "type": "natural_event",
  "source": "NASA EONET",
  "event_id": "EONET_12345",
  "title": "Wildfire in California",
  "time": "2025-12-23T10:00:00",
  "latitude": 34.0522,
  "longitude": -118.2437,
  "categories": ["Wildfires"]
}
```

### Flood Risk Data (flood_risk.json)
```json
{
  "events": [
    {
      "location": "New Orleans",
      "time": "2025-12-23 T00:00:00",
      "risk_level": "high",
      "river_discharge": 1500.5
    }
  ],
  "generated_at": "2025-12-23T12:00:00"
}
```

## Outputs

### Data Files

Processed data is stored in `data/` directory:
- `earthquakes_<timestamp>.json` - Cleaned earthquake data (latest 5 files kept)
- `weather_all.json` - Combined weather data for all cities
- `wildfires.json` - Wildfire events
- `storms.json` - Storm events
- `volcanoes.json` - Volcano events
- `flood_risk.json` - Flood risk data
- `eonet_events.json` - General EONET events

### Log Files

System logs in `logs/app.log`:
```
2025-12-21T00:38:00+03:00 [INFO] RuntimeSystem initialized
2025-12-21T00:38:05 [INFO] Fetching data from USGSEarthquakeSource...
2025-12-21T00:38:07 [INFO] Successfully fetched 37 items from USGSEarthquakeSource
```

**Note**: Log files are automatically cleaned when they exceed 5MB.

## Configuration

Settings in `config.py`:
- `OPENWEATHER_API_KEY` - OpenWeather API key
- `USGS_API_URL` - USGS API endpoint (default can be used)

Can also be set as environment variable:
```bash
set OPENWEATHER_API_KEY=your_api_key_here
```

## Technologies

- **Python 3.8+**
- **Flask** - Web framework
- **Threading** - Concurrent execution
- **Queue** - Thread-safe communication
- **Requests** - HTTP client
- **BeautifulSoup4** - Web scraping
- **Leaflet.js** - Map visualization
- **JSON** - Data storage format

## Python Concepts

- Object-Oriented Programming
- Threading & Concurrency
- Queue-based Communication
- Producer-Consumer Pattern
- Exception Handling
- Type Hints
- Modular Architecture
- Design Patterns

## Troubleshooting

### Weather Data Not Showing
1. Ensure `main_runtime.py` has been run
2. Check that `data/weather_all.json` file exists
3. Verify API key is correctly configured

### Earthquake Data Not Showing
1. Ensure `main_runtime.py` has been run
2. Check that `data/earthquakes_*.json` files exist
3. Check internet connection

### Forecast Data Not Showing
1. Ensure `main_runtime.py` has been run (forecast enabled)
2. Check that `weather_all.json` contains entries with `type: "weather_forecast"`

### Natural Events Not Showing
1. Ensure `main_runtime.py` has been run
2. Check that respective JSON files exist (`wildfires.json`, `storms.json`, `volcanoes.json`)
3. Verify NASA EONET API is accessible

### Seismic Risk Analysis Not Working
1. Ensure earthquake data has been fetched
2. Check that fault line data is properly configured
3. Verify coordinate ranges are within Americas boundaries

## License and Credits

This project was developed as part of COMP303 - Advanced Python Programming course.

**Instructor:** Dr. Öğr. Üyesi Ali Cihan Keleş  
**Semester:** 2024-2025  
**Course:** COMP303

## Contact

For questions, please contact team members.

© 2025 SDEWS Team - COMP303 Project


### Data Files

Processed data is stored in `data/` directory:
- `earthquakes_<timestamp>.json` - Cleaned earthquake data (latest 5 files kept)
- `weather_all.json` - Combined weather data for all cities
- `wildfires.json` - Wildfire events
- `storms.json` - Storm events
- `volcanoes.json` - Volcano events
- `flood_risk.json` - Flood risk data
- `eonet_events.json` - General EONET events

### Log Files

System logs in `logs/app.log`:
```
2025-12-21T00:38:00+03:00 [INFO] RuntimeSystem initialized
2025-12-21T00:38:05 [INFO] Fetching data from USGSEarthquakeSource...
2025-12-21T00:38:07 [INFO] Successfully fetched 37 items from USGSEarthquakeSource
```

**Note**: Log files are automatically cleaned when they exceed 5MB.

## Configuration

Settings in `config.py`:
- `OPENWEATHER_API_KEY` - OpenWeather API key
- `USGS_API_URL` - USGS API endpoint (default can be used)

Can also be set as environment variable:
```bash
set OPENWEATHER_API_KEY=your_api_key_here
```

## Technologies

- **Python 3.8+**
- **Flask** - Web framework
- **Threading** - Concurrent execution
- **Queue** - Thread-safe communication
- **Requests** - HTTP client
- **BeautifulSoup4** - Web scraping
- **Leaflet.js** - Map visualization
- **JSON** - Data storage format

## Python Concepts

- Object-Oriented Programming
- Threading & Concurrency
- Queue-based Communication
- Producer-Consumer Pattern
- Exception Handling
- Type Hints
- Modular Architecture
- Design Patterns

## Troubleshooting

### Weather Data Not Showing
1. Ensure `main_runtime.py` has been run
2. Check that `data/weather_all.json` file exists
3. Verify API key is correctly configured

### Earthquake Data Not Showing
1. Ensure `main_runtime.py` has been run
2. Check that `data/earthquakes_*.json` files exist
3. Check internet connection

### Forecast Data Not Showing
1. Ensure `main_runtime.py` has been run (forecast enabled)
2. Check that `weather_all.json` contains entries with `type: "weather_forecast"`

### Natural Events Not Showing
1. Ensure `main_runtime.py` has been run
2. Check that respective JSON files exist (`wildfires.json`, `storms.json`, `volcanoes.json`)
3. Verify NASA EONET API is accessible

### Seismic Risk Analysis Not Working
1. Ensure earthquake data has been fetched
2. Check that fault line data is properly configured
3. Verify coordinate ranges are within Americas boundaries

## License and Credits

This project was developed as part of COMP303 - Advanced Python Programming course.

**Instructor:** Dr. Öğr. Üyesi Ali Cihan Keleş  
**Semester:** 2024-2025  
**Course:** COMP303

## Contact

For questions, please contact team members.

© 2025 SDEWS Team - COMP303 Project