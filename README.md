# SDEWS - Smart Disaster Early Warning System

## 📋 Proje Özeti
SDEWS, deprem, hava durumu ve haber kaynaklarından gerçek zamanlı veri toplayan, işleyen ve analiz eden Python tabanlı bir afet erken uyarı sistemidir.

## 👥 Ekip ve Sorumluluklar

| Üye | Rol | Sorumluluklar |
|-----|-----|---------------|
| **Hakan Demircan** | API Integration & Web Scraping | `datasources/` - USGS, OpenWeather API, News scraping |
| **Erdem Kaya** | Core System & Data Models | `models/` - RawEarthquake, CleanedEarthquake |
| **Yağız Efe Hüşan** | Data Processing & Analytics | `processing/` - Storage, data cleaning, analytics |
| **Fikret Ahıskalı** | Concurrency & Runtime Pipeline | `pipeline/` - Threading, queues, orchestration |

## 🏗️ Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────┐
│                  RuntimeSystem                          │
│         (Ana Orkestratör - Fikret)                     │
└────────────┬──────────────────────┬────────────────────┘
             │                      │
    ┌────────▼────────┐    ┌───────▼──────────┐
    │ DataSourceMgr   │    │  EventPipeline   │
    │  (Producer)     │───>│   (Consumer)     │
    └────────┬────────┘    └───────┬──────────┘
             │                      │
    ┌────────▼────────┐    ┌───────▼──────────┐
    │  Data Sources   │    │   Processing     │
    │   (Hakan)       │    │     (Efe)        │
    └─────────────────┘    └──────────────────┘
```

## 📁 Proje Yapısı

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
│   ├── data_processing.py
│   └── analytics.py
├── pipeline/             # Fikret - Concurrency & Pipeline
│   ├── data_source_manager.py
│   ├── event_pipeline.py
│   └── runtime_system.py
├── data/                 # İşlenmiş veriler (JSON/CSV)
├── logs/                 # Sistem logları
├── main_runtime.py       # Ana çalıştırma dosyası
├── app.py                # Flask API server (alternatif)
├── test_runtime.py       # Test dosyası
└── requirements.txt      # Python bağımlılıkları
```

## 🚀 Kurulum

```bash
# Virtual environment oluştur
python -m venv venv

# Aktive et (Windows)
venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

## 💻 Kullanım

### Sürekli Mod (Continuous)
```bash
python main_runtime.py
```
- Her 2 dakikada bir veri çeker
- Ctrl+C ile durdurulana kadar çalışır

### Tek Çalıştırma Modu (Single Run)
```bash
python main_runtime.py --once
```
- Bir kez veri çeker ve çıkar
- Test için idealdir

### Flask API Server (Alternatif)
```bash
python app.py
```

API Endpoints:
- `GET /` - Health check
- `GET /api/earthquakes` - Deprem verileri
- `GET /api/weather?city=Istanbul` - Hava durumu
- `GET /api/news` - Haber başlıkları

### Test Çalıştırma
```bash
python test_runtime.py
```

## ✨ Özellikler

### 🔄 Concurrency (Fikret)
- Multi-threaded data fetching
- Thread-safe queue communication
- Producer-consumer pattern
- Lock-based synchronization

### 📊 Data Processing (Efe)
- Data cleaning ve normalization
- JSON/CSV storage
- Statistical analysis
- Event filtering

### 🌐 Data Sources (Hakan)
- USGS Earthquake API
- OpenWeather API
- Web scraping (CNN, NTV)

### 🏗️ Core Models (Erdem)
- RawEarthquake model
- CleanedEarthquake model
- Data validation

## 📝 Konfigürasyon

`config.py` dosyasını düzenleyerek:
- API anahtarlarını ayarlayın
- Fetch interval'i değiştirin
- Şehir lokasyonlarını belirleyin

## 📊 Çıktılar

İşlenmiş veriler `data/` klasöründe saklanır:
- `earthquakes_<timestamp>.json` - Temizlenmiş deprem verileri
- `weather_<timestamp>.json` - Hava durumu verileri

Loglar `logs/app.log` dosyasında:
```
2025-12-21T00:38:00+03:00 [INFO] RuntimeSystem initialized
2025-12-21T00:38:05 [INFO] Fetching data from USGSEarthquakeSource...
```

## 🔧 Teknolojiler

- **Python 3.x**
- **Threading** - Concurrent execution
- **Queue** - Thread-safe communication
- **Requests** - HTTP client
- **BeautifulSoup4** - Web scraping
- **Flask** - API server

## 📚 Python Konceptleri

✅ Object-Oriented Programming
✅ Threading & Concurrency
✅ Queue-based Communication
✅ Producer-Consumer Pattern
✅ Exception Handling
✅ Type Hints
✅ Modular Architecture

## 🎓 Kurs Bilgisi

**Kurs:** COMP303 - Advanced Python Programming
**Öğretim Görevlisi:** Dr. Öğr. Üyesi Ali Cihan Keleş
**Dönem:** 2024-2025

---

## 📞 İletişim

Sorularınız için ekip üyeleriyle iletişime geçebilirsiniz.

**© 2025 SDEWS Team - COMP303 Project**
