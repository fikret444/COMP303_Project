# SDEWS Çalıştırma Rehberi

## Hızlı Başlangıç

### 1. Bağımlılıkları Yükle (İsteğe Bağlı)
```bash
pip install Flask requests beautifulsoup4 python-dotenv tzdata pytest
```
Not: lxml kurulumu başarısız olabilir (C++ build tools gerekiyor), ama proje çalışır.

### 2. API Key Kontrolü
`config.py` dosyasında OpenWeather API key var mı kontrol edin. Varsa hazırsınız!

### 3. Çalıştırma Seçenekleri

#### A) Veri Toplama Sistemi (Ana Sistem)
```bash
# Sürekli mod (Ctrl+C ile durdur)
python main_runtime.py

# Tek çalıştırma (test için)
python main_runtime.py --once
```

#### B) Web Dashboard
```bash
python dashboard.py
```
Tarayıcıda: http://localhost:5000

## Ne Yapıyor?

### main_runtime.py
- USGS'ten deprem verileri çeker
- OpenWeather'dan 6 şehir için hava durumu çeker (Istanbul, Ankara, Izmir, Antalya, Bursa, Adana)
- Verileri `data/` klasörüne JSON olarak kaydeder
- Her 2 dakikada bir otomatik güncelleme yapar

### dashboard.py
- Web arayüzü sunar
- Deprem ve hava durumu verilerini görselleştirir
- Harita üzerinde marker'lar gösterir
- API endpoint'leri sağlar

## API Endpoints

- `GET /api/earthquakes` - Deprem verileri
- `GET /api/weather` - Hava durumu
- `GET /api/forecast` - 5 günlük tahmin
- `GET /api/alerts` - Uyarılar
- `GET /api/news` - Haberler

## Sorun Giderme

### Import hatası alıyorsanız:
```bash
# COMP303_Project klasöründen çalıştırdığınızdan emin olun
cd COMP303_Project
python main_runtime.py
```

### API key hatası:
`config.py` dosyasında `OPENWEATHER_API_KEY` kontrol edin.

### Port zaten kullanılıyor:
Dashboard farklı portta çalıştırın:
```python
# dashboard.py içinde
app.run(port=5001)
```

