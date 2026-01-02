# SDEWS - Smart Disaster Early Warning System

## Proje Özeti

SDEWS, deprem, hava durumu ve haber kaynaklarından gerçek zamanlı veri toplayan, işleyen ve analiz eden Python tabanlı bir afet erken uyarı sistemidir. Sistem, çoklu veri kaynaklarından eşzamanlı veri çekme, veri işleme ve web tabanlı görselleştirme özellikleri sunar.

## Ekip ve Sorumluluklar

| Üye | Rol | Sorumluluklar |
|-----|-----|---------------|
| **Hakan Demircan** | API Integration & Web Scraping | `datasources/` - USGS, OpenWeather API, News scraping |
| **Erdem Kaya** | Core System & Data Models | `models/` - RawEarthquake, CleanedEarthquake |
| **Yağız Efe Hüşan** | Data Processing & Analytics | `processing/` - Storage, data cleaning, analytics |
| **Fikret Ahıskalı** | Concurrency & Runtime Pipeline | `pipeline/` - Threading, queues, orchestration |

## Sistem Mimarisi

Sistem Producer-Consumer pattern kullanarak çoklu thread'lerle veri çekme ve işleme yapar:

```
RuntimeSystem (Ana Orkestratör)
    ├── DataSourceManager (Producer)
    │   ├── USGSEarthquakeSource
    │   └── OpenWeatherSource (6 şehir)
    │
    └── EventPipeline (Consumer)
        ├── Data Cleaning (Efe)
        ├── Analytics (Efe)
        └── Storage (Efe)
```

## Proje Yapısı

```
COMP303_Project/
├── datasources/          # Hakan - API & Web Scraping
│   ├── usgs_earthquake.py
│   ├── openweather_source.py
│   └── scraping/
│       └── scrape_news.py
├── models/               # Erdem - Core Data Models
│   ├── raw_earthquake.py
│   └── cleaned_earthquake.py
├── processing/           # Efe - Data Processing
│   ├── storage.py
│   ├── earthquake_processing.py
│   └── analytics.py
├── pipeline/             # Fikret - Concurrency & Pipeline
│   ├── data_source_manager.py
│   ├── event_pipeline.py
│   └── runtime_system.py
├── templates/            # Web Dashboard
│   └── dashboard.html
├── data/                 # İşlenmiş veriler (JSON)
├── logs/                 # Sistem logları
├── main_runtime.py       # Ana çalıştırma dosyası
├── dashboard.py          # Flask web dashboard
├── config.py             # API anahtarları ve ayarlar
└── requirements.txt      # Python bağımlılıkları
```

## Kurulum

### Gereksinimler

- Python 3.8 veya üzeri
- OpenWeather API anahtarı (isteğe bağlı, hava durumu için)
- USGS API anahtarı gerekmez (ücretsiz)

### Adımlar

1. Projeyi klonlayın veya indirin
2. Virtual environment oluşturun:
   ```bash
   python -m venv venv
   ```

3. Virtual environment'ı aktif edin:
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

4. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

5. API anahtarlarını ayarlayın:
   - `config.py` dosyasını düzenleyin veya
   - Environment variable olarak ayarlayın:
     ```bash
     set OPENWEATHER_API_KEY=your_api_key_here
     ```

## Kullanım

### Veri Toplama Sistemi

#### Sürekli Mod (Continuous)
```bash
python main_runtime.py
```
- Her 2 dakikada bir veri çeker
- Ctrl+C ile durdurulana kadar çalışır
- Veriler `data/` klasörüne kaydedilir

#### Tek Çalıştırma Modu (Single Run)
```bash
python main_runtime.py --once
```
- Bir kez veri çeker ve çıkar
- Test için idealdir

### Web Dashboard

#### Dashboard'u Başlatma
```bash
python dashboard.py
```

Tarayıcıda şu adresi açın:
```
http://localhost:5000
```

#### Dashboard Özellikleri

- Harita görünümü: Deprem ve hava durumu marker'ları
- Deprem listesi: Son depremler ve detayları
- Hava durumu: 6 şehir için anlık ve forecast verileri
- Uyarılar: Mevcut durum ve ileriye dönük uyarılar
- Haberler: Risk içeren haber başlıkları

#### API Endpoints

- `GET /` - Dashboard ana sayfası
- `GET /api/earthquakes` - Deprem verileri ve istatistikler
- `GET /api/weather` - Anlık hava durumu verileri
- `GET /api/forecast` - 5 günlük hava durumu tahminleri
- `GET /api/forecast/<city>` - Belirli şehir için forecast
- `GET /api/alerts` - Tüm uyarılar (current + forecast)
- `GET /api/alerts/current` - Mevcut durumdan kaynaklanan uyarılar
- `GET /api/alerts/forecast` - İleriye dönük uyarılar
- `GET /api/news` - Risk içeren haber başlıkları
- `GET /api/all` - Tüm veriler (deprem + hava durumu + forecast)

## Özellikler

### Veri Kaynakları (Hakan)

- **USGS Earthquake API**: Son 24 saatteki deprem verileri
- **OpenWeather API**: 
  - Anlık hava durumu (6 şehir: Istanbul, Ankara, Izmir, Antalya, Bursa, Adana)
  - 5 günlük forecast (3 saatlik aralıklarla)
- **Web Scraping**: NTV ve CNN Türk'ten risk içeren haber başlıkları

### Veri İşleme (Efe)

- Veri temizleme ve normalizasyon
- JSON formatında saklama
- İstatistiksel analiz (ortalama, min, max magnitude)
- Event filtreleme (magnitude, bölge, zaman)

### Concurrency (Fikret)

- Multi-threaded veri çekme
- Producer-Consumer pattern
- Thread-safe queue iletişimi
- Lock-based senkronizasyon

### Data Models (Erdem)

- RawEarthquake: Ham deprem verisi modeli
- CleanedEarthquake: Temizlenmiş deprem verisi modeli
- Veri validasyonu ve tip kontrolü

### Alert Sistemi

Sistem otomatik olarak uyarılar oluşturur:

**Mevcut Durum Uyarıları:**
- Deprem: Magnitude >= 5.0
- Hava Durumu:
  - Aşırı sıcak (>= 35°C)
  - Aşırı soğuk (<= -5°C)
  - Yüksek rüzgar (>= 15 m/s)
  - Yüksek nem (>= 90%)
  - Düşük basınç (<= 1000 hPa)
  - Düşük görüş mesafesi (<= 1000m)
  - Yağış, kar, yoğun bulutluluk

**İleriye Dönük Uyarılar (Forecast):**
- Düşük/yüksek sıcaklık tahminleri
- Yüksek rüzgar tahminleri
- Kar yağışı tahminleri
- Yağış tahminleri
- Düşük basınç tahminleri

## Veri Formatları

### Deprem Verisi (earthquakes_*.json)
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

### Hava Durumu Verisi (weather_all.json)
```json
{
  "type": "weather",
  "source": "OpenWeatherMap",
  "location": "Istanbul",
  "temperature": 10.09,
  "feels_like": 8.5,
  "humidity": 87,
  "pressure": 1013,
  "wind_speed": 4.12,
  "wind_direction": 270,
  "clouds": 75,
  "precipitation": 0,
  "visibility": 10000,
  "latitude": 41.0351,
  "longitude": 28.9833,
  "time": "2025-12-23T11:32:11"
}
```

### Forecast Verisi
```json
{
  "type": "weather_forecast",
  "location": "Istanbul",
  "forecast_time": "2025-12-23T15:00:00",
  "temperature": 12.5,
  "precipitation": 2.3,
  "clouds": 80,
  "humidity": 85
}
```

## Çıktılar

### Veri Dosyaları

İşlenmiş veriler `data/` klasöründe saklanır:
- `earthquakes_<timestamp>.json` - Temizlenmiş deprem verileri
- `weather_all.json` - Tüm şehirler için birleşik hava durumu ve forecast verileri

### Log Dosyaları

Sistem logları `logs/app.log` dosyasında:
```
2025-12-21T00:38:00+03:00 [INFO] RuntimeSystem initialized
2025-12-21T00:38:05 [INFO] Fetching data from USGSEarthquakeSource...
2025-12-21T00:38:07 [INFO] Successfully fetched 37 items from USGSEarthquakeSource
```

## Konfigürasyon

`config.py` dosyasında ayarlanabilir:
- `OPENWEATHER_API_KEY` - OpenWeather API anahtarı
- `USGS_API_URL` - USGS API endpoint (varsayılan kullanılabilir)

Environment variable olarak da ayarlanabilir:
```bash
set OPENWEATHER_API_KEY=your_api_key_here
```

## Teknolojiler

- **Python 3.8+**
- **Flask** - Web framework
- **Threading** - Concurrent execution
- **Queue** - Thread-safe communication
- **Requests** - HTTP client
- **BeautifulSoup4** - Web scraping
- **Leaflet.js** - Harita görselleştirme
- **JSON** - Veri saklama formatı

## Python Konseptleri

- Object-Oriented Programming
- Threading & Concurrency
- Queue-based Communication
- Producer-Consumer Pattern
- Exception Handling
- Type Hints
- Modular Architecture
- Design Patterns

## Test

### Runtime Testi
```bash
python test_runtime.py
```

### Import Testi
```bash
python test_imports.py
```

### News Scraper Testi
```bash
python test_news_scraper.py
```

## Sorun Giderme

### Hava Durumu Verisi Görünmüyor
1. `main_runtime.py` çalıştırıldığından emin olun
2. `data/weather_all.json` dosyasının var olduğunu kontrol edin
3. API anahtarının doğru ayarlandığını kontrol edin

### Deprem Verisi Görünmüyor
1. `main_runtime.py` çalıştırıldığından emin olun
2. `data/earthquakes_*.json` dosyalarının var olduğunu kontrol edin
3. İnternet bağlantısını kontrol edin

### Forecast Verileri Görünmüyor
1. `main_runtime.py` çalıştırıldığından emin olun (forecast aktif)
2. `weather_all.json` dosyasında `type: "weather_forecast"` olan verilerin olduğunu kontrol edin

## Lisans ve Krediler

Bu proje COMP303 - Advanced Python Programming dersi kapsamında geliştirilmiştir.

**Öğretim Görevlisi:** Dr. Öğr. Üyesi Ali Cihan Keleş  
**Dönem:** 2024-2025  
**Kurs:** COMP303

## İletişim

Sorularınız için ekip üyeleriyle iletişime geçebilirsiniz.

© 2025 SDEWS Team - COMP303 Project
