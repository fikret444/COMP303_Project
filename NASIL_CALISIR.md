# SDEWS - Sistem Nasıl Çalışır?

## 🎬 ADIM ADIM NE OLUYOR?

### 1️⃣ BAŞLATMA (python main_runtime.py --once)

```
============================================================

      Smart Disaster Early Warning System (SDEWS)

  Concurrent Data Processing & Real-time Event Pipeline

============================================================

Ekip Uyeleri:
- Hakan Demircan: API Integration & Web Scraping
- Erdem Kaya: Core System & Data Models
- Fikret Ahiskali: Concurrency & Runtime Pipeline
- Yagiz Efe Husan: Data Processing, Storage & Analytics
```

**Ne Oluyor?**
- Banner gösteriliyor
- Sistem başlatılıyor

---

### 2️⃣ DATA SOURCE'LAR HAZIRLANIYOR

**Log'da görünen:**
```
[INFO] Data source'lar baslatiliyor...
[INFO] [OK] USGS Earthquake Source hazir
[INFO] [OK] OpenWeather Source hazir
[INFO] Runtime system olusturuluyor...
[INFO] [OK] Runtime System hazir
```

**Arka planda:**
```
┌─────────────────────────────────────┐
│   Hakan'ın Data Source'ları         │
├─────────────────────────────────────┤
│  1. USGSEarthquakeSource            │
│     - API: earthquake.usgs.gov      │
│     - Son 24 saatin depremleri      │
│                                     │
│  2. OpenWeatherSource               │
│     - API: openweathermap.org       │
│     - Istanbul hava durumu          │
└─────────────────────────────────────┘
```

---

### 3️⃣ PİPELİNE SİSTEMİ BAŞLIYOR (Fikret'in Çalışması)

**Log'da görünen:**
```
[INFO] DataSourceManager initialized with 2 sources
[INFO] EventPipeline initialized with 3 consumers
[INFO] RuntimeSystem initialized
```

**Arka planda:**
```
┌─────────────────────────────────────────────────────────┐
│              RUNTIME SYSTEM (Ana Orkestratör)           │
└─────────────────┬───────────────────────┬───────────────┘
                  │                       │
      ┌───────────▼───────────┐  ┌───────▼──────────────┐
      │ DataSourceManager     │  │  EventPipeline       │
      │ (Producer)            │  │  (Consumer)          │
      │                       │  │                      │
      │ - 2 data sources      │  │ - 3 worker threads   │
      │ - Thread pool         │  │ - Queue processing   │
      │ - Concurrent fetch    │  │ - Data cleaning      │
      └───────────────────────┘  └──────────────────────┘
```

---

### 4️⃣ VERİ ÇEKME BAŞLIYOR (CONCURRENT - PARALEL)

**Log'da görünen:**
```
[INFO] Starting concurrent fetch from 2 sources
[INFO] Fetching data from USGSEarthquakeSource...
[INFO] Fetching data from OpenWeatherSource...
```

**Arka planda (THREADING):**
```
          MAIN THREAD
               |
    ┌──────────┴──────────┐
    │                     │
┌───▼────┐          ┌─────▼────┐
│Thread 1│          │ Thread 2 │
│        │          │          │
│ USGS   │          │ Weather  │
│ API    │          │ API      │
│        │          │          │
│ 🌍     │          │ ☁️       │
└───┬────┘          └─────┬────┘
    │                     │
    └──────────┬──────────┘
               │
          QUEUE (Thread-safe)
```

**Gerçek Durum:**
- İki thread AYNI ANDA çalışıyor (paralel)
- USGS API'ye gidiyor → 38 deprem verisi alıyor
- Weather API'ye gidiyor → Istanbul hava durumu alıyor
- Her ikisi de bitince queue'ya koyuyor

---

### 5️⃣ VERİ GELDİ! (USGS'den 38 deprem)

**Log'da görünen:**
```
[INFO] Successfully fetched 38 items from USGSEarthquakeSource
[INFO] All fetch operations completed
[INFO] Added 1 event batches to pipeline
```

**Queue'da ne var:**
```
Queue:
┌────────────────────────────────────────────┐
│ Event 1:                                   │
│ - source: "USGSEarthquakeSource"          │
│ - data: [38 earthquake records]           │
│ - timestamp: 1766267481                   │
└────────────────────────────────────────────┘
```

---

### 6️⃣ CONSUMER WORKER'LAR İŞLİYOR (Fikret'in Pipeline'ı)

**Log'da görünen:**
```
[INFO] Starting 3 consumer workers
[INFO] Consumer worker 0 started
[INFO] Consumer worker 1 started
[INFO] Consumer worker 2 started
[INFO] Worker 1 processing event from USGSEarthquakeSource
```

**Arka planda (Producer-Consumer Pattern):**
```
INPUT QUEUE          WORKERS          OUTPUT QUEUE
┌─────────┐      ┌──────────┐      ┌─────────┐
│ Event 1 │──────┤ Worker 0 │      │         │
│ Event 2 │──────┤ Worker 1 │──────┤ Result 1│
│ Event 3 │──────┤ Worker 2 │      │ Result 2│
└─────────┘      └──────────┘      └─────────┘
   (Empty)       (Processing)       (Ready)
```

**Worker 1 ne yapıyor?**
1. Queue'dan event alıyor
2. Source'a bakıyor: "USGSEarthquakeSource"
3. Earthquake processor'ü çağırıyor
4. Efe'nin data processing fonksiyonlarını kullanıyor

---

### 7️⃣ VERİ TEMİZLENİYOR (Efe'nin İşi)

**Log'da görünen:**
```
[INFO] Temizlenen event sayisi: 38
```

**Arka planda (Efe'nin Processing Modülü):**
```python
# processing/data_processing.py

def clean_usgs_earthquake_events(usgs_events):
    # Ham veri:
    {
        "type": "earthquake",
        "mag": 5.2,
        "place": "Chile",
        "time": 1734736224538,  # Epoch time (ms)
        ...
    }
    
    # Temizleniyor:
    {
        "id": 1,
        "event_type": "earthquake",
        "magnitude": 5.2,
        "location": "112 km SSE of Colchane, Chile",
        "timestamp": "2025-12-20T23:30:24.538000",  # ISO format
        "latitude": -20.1456,
        "longitude": -68.0803
    }
```

**Ne yapılıyor?**
1. ✅ Eksik alanlar kontrol ediliyor
2. ✅ Magnitude float'a çevriliyor
3. ✅ Zaman epoch'tan ISO formatına
4. ✅ Koordinatlar validate ediliyor
5. ✅ Geçersiz veriler atılıyor

---

### 8️⃣ İSTATİSTİKLER HESAPLANIYOR (Efe'nin Analytics)

**Log'da görünen:**
```
[INFO]   Statistics:
[INFO]     - Total events: 38
[INFO]     - Max magnitude: 5.60
[INFO]     - Avg magnitude: 3.69
```

**Arka planda:**
```python
# processing/analytics.py

def compute_basic_stats(events):
    magnitudes = [e['magnitude'] for e in events]
    
    return {
        'total_events': len(events),           # 38
        'max_magnitude': max(magnitudes),      # 5.60
        'min_magnitude': min(magnitudes),      # 2.47
        'avg_magnitude': sum(magnitudes) / len(magnitudes)  # 3.69
    }
```

---

### 9️⃣ VERİ KAYDEDİLİYOR (Efe'nin Storage)

**Log'da görünen:**
```
[INFO]   Saved to: earthquakes_1766267481.json
```

**Arka planda:**
```python
# processing/storage.py

def save_events_to_json(events, filename):
    file_path = DATA_DIR / filename  # data/earthquakes_1766267481.json
    
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
```

**Kaydedilen dosya:**
```json
// data/earthquakes_1766267481.json
[
  {
    "id": 1,
    "event_type": "earthquake",
    "timestamp": "2025-12-21T00:23:42.890000",
    "location": "8 km SW of Guǎnica, Puerto Rico",
    "magnitude": 2.47,
    "latitude": 17.9195,
    "longitude": -66.9663333333333
  },
  {
    "id": 2,
    ...
  }
  // ... 38 events total
]
```

---

### 🔟 SONUÇLAR GÖSTER İLİYOR

**Log'da görünen:**
```
============================================================
PROCESSING RESULTS
============================================================
Result #1 - USGSEarthquakeSource: SUCCESS
  Events processed: 38
  Statistics:
    - Total events: 38
    - Max magnitude: 5.60
    - Avg magnitude: 3.69
  Saved to: earthquakes_1766267481.json
------------------------------------------------------------
```

**Console'da ne görüyorsun:**
```
✓ USGS'den 38 deprem verisi alındı
✓ Veriler temizlendi
✓ İstatistikler hesaplandı
✓ Dosyaya kaydedildi
✓ İşlem başarılı!
```

---

### 1️⃣1️⃣ SİSTEM DURDURULUYOR

**Log'da görünen:**
```
[INFO] Stopping RuntimeSystem...
[INFO] Stopping consumer workers...
[INFO] Consumer worker 1 stopped
[INFO] Consumer worker 0 stopped
[INFO] Consumer worker 2 stopped
[INFO] All consumer workers stopped
============================================================
SYSTEM STATUS
============================================================
Uptime: 0 seconds
Cycles completed: 1
Data Sources: 2
Processed events: 1
Errors: 0
============================================================
SDEWS Runtime System Stopped
============================================================
```

**Arka planda:**
```
1. Consumer thread'lere "poison pill" gönderiliyor (None)
2. Her thread gracefully duruyor
3. Queue'lar temizleniyor
4. Final durum raporu
5. Program çıkıyor
```

---

## 📊 TÜM SÜREÇ VİZÜALİZASYONU

```
BAŞLANGIÇ
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  RUNTIME SYSTEM BAŞLIYOR (main_runtime.py)              │
│  - Banner göster                                         │
│  - Data sources hazırla (Hakan'ın kodları)             │
│  - Pipeline başlat (Fikret'in kodları)                 │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  VERİ ÇEKME BAŞLIYOR (DataSourceManager)               │
│  ┌─────────────┐              ┌──────────────┐        │
│  │ Thread 1    │              │  Thread 2    │        │
│  │ USGS API    │──Paralel──┤  │  Weather API │        │
│  │ 38 deprem   │              │  1 hava data │        │
│  └─────────────┘              └──────────────┘        │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  QUEUE'YA KONUYOR (Thread-safe)                        │
│  [Event: USGS - 38 records]                            │
│  [Event: Weather - 1 record]                           │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  CONSUMER WORKERS İŞLİYOR (EventPipeline)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Worker 0 │  │ Worker 1 │  │ Worker 2 │            │
│  │ Bekliyor │  │ İşliyor  │  │ Bekliyor │            │
│  └──────────┘  └──────────┘  └──────────┘            │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  VERİ İŞLENİYOR (Efe'nin Processing + Erdem'in Model)  │
│  1. Ham veri al                                         │
│  2. Temizle (clean_usgs_earthquake_events)             │
│  3. Validate et                                         │
│  4. İstatistik hesapla (compute_basic_stats)           │
│  5. JSON'a kaydet (save_events_to_json)                │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  SONUÇ ÜRETİLİYOR                                       │
│  - success: True                                        │
│  - event_count: 38                                      │
│  - stats: {max: 5.6, avg: 3.69}                        │
│  - filename: earthquakes_1766267481.json                │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  RAPOR GÖSTER (Console + Log)                          │
│  ✓ 38 events processed                                  │
│  ✓ Max magnitude: 5.60                                  │
│  ✓ Saved to: earthquakes_1766267481.json               │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  SİSTEM DURDUR (Graceful Shutdown)                     │
│  - Consumer thread'leri durdur                          │
│  - Queue'ları temizle                                   │
│  - Final status göster                                  │
│  - Program çık                                          │
└─────────────────────────────────────────────────────────┘
    │
    ▼
   BİTİŞ
```

---

## 🎯 HANGİ DOSYALAR OLUŞUYOR?

### 1. data/earthquakes_1766267481.json
```json
[
  {
    "id": 1,
    "event_type": "earthquake",
    "timestamp": "2025-12-21T00:23:42.890000",
    "location": "8 km SW of Guǎnica, Puerto Rico",
    "magnitude": 2.47,
    "latitude": 17.9195,
    "longitude": -66.9663333333333
  },
  ...38 events total
]
```

### 2. logs/app.log
```
2025-12-21T00:51:21.983790+03:00 [INFO] SDEWS System Initialization
2025-12-21T00:51:21.984347+03:00 [INFO] DataSourceManager initialized
2025-12-21T00:51:21.984806+03:00 [INFO] Starting concurrent fetch
...tüm sistem logları
```

---

## ⚙️ HANGİ KOMPONENT NE YAPIYOR?

| Komponent | Sorumlu | Ne Yapıyor? |
|-----------|---------|-------------|
| **USGSEarthquakeSource** | Hakan | USGS API'den deprem verisi çeker |
| **OpenWeatherSource** | Hakan | OpenWeather API'den hava durumu çeker |
| **RawEarthquake** | Erdem | Ham deprem verisi için model |
| **CleanedEarthquake** | Erdem | Temizlenmiş deprem verisi için model |
| **storage.py** | Efe | JSON/CSV kaydetme, loglama |
| **data_processing.py** | Efe | Veri temizleme, normalizasyon |
| **analytics.py** | Efe | İstatistik hesaplama, filtreleme |
| **DataSourceManager** | Fikret | Multi-threaded veri çekme |
| **EventPipeline** | Fikret | Producer-consumer processing |
| **RuntimeSystem** | Fikret | Tüm sistemi orkestra ediyor |

---

## 🔄 SÜREKLI MOD (--once olmadan)

```bash
python main_runtime.py
```

**Ne fark var?**
```
Döngü 1: Veri çek → İşle → Kaydet → 2 dk bekle
Döngü 2: Veri çek → İşle → Kaydet → 2 dk bekle
Döngü 3: Veri çek → İşle → Kaydet → 2 dk bekle
...
Ctrl+C → Durdur
```

**Her 2 dakikada:**
- Yeni deprem verileri çekiliyor
- Yeni dosya oluşuyor: earthquakes_<timestamp>.json
- Loglar büyüyor
- Sistem çalışmaya devam ediyor

---

## 💡 ÖZET: 5 KELİMEDE NE OLUYOR?

1. **VERİ ÇEK** → Paralel thread'lerle API'lerden
2. **QUEUE'YA KOY** → Thread-safe şekilde
3. **İŞLE** → Consumer worker'lar temizliyor
4. **KAYDET** → JSON dosyasına + log
5. **RAPOR** → Console ve log'a yazdır

---

## 🎓 ÖĞRENME DEĞERİ

Bu projede gösteriliyor:
- ✅ **Threading & Concurrency** → Paralel veri çekme
- ✅ **Producer-Consumer Pattern** → Queue-based processing
- ✅ **Modular Architecture** → Her ekip üyesi kendi modülü
- ✅ **Data Pipeline** → Raw → Clean → Process → Store
- ✅ **Error Handling** → Try-catch, timeout, graceful shutdown
- ✅ **Logging** → Her adım loglanıyor
- ✅ **Team Collaboration** → 4 kişinin kodu entegre

---

**Kısacası:** Gerçek zamanlı bir afet izleme sistemi! 🌍🔥

