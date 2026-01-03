"""
SDEWS Web Dashboard
Tarayıcıda görsel deprem takip sistemi
"""

from flask import Flask, render_template, jsonify, request
import json
import os
import glob
from datetime import datetime, timedelta
from pathlib import Path
from processing.storage import cleanup_old_files
from processing.seismic_risk_analyzer import SeismicRiskAnalyzer, analyze_seismic_risk

# Scraping modülü - artık BeautifulSoup4 ile de çalışır
try:
    from datasources.scraping.scrape_news import scrape_all_risk_headlines
    SCRAPING_AVAILABLE = True
except ImportError as e:
    SCRAPING_AVAILABLE = False
    def scrape_all_risk_headlines():
        return []

# EONET modülü
try:
    from datasources.eonet_source import EONETSource
    EONET_AVAILABLE = True
except ImportError as e:
    EONET_AVAILABLE = False

app = Flask(__name__)

# Dashboard'un çalıştığı dizini bul
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

def get_latest_earthquake_file():
    """En son oluşturulan deprem dosyasını bul"""
    pattern = str(DATA_DIR / "earthquakes_*.json")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def get_latest_weather_file():
    """En son oluşturulan hava durumu dosyasını bul"""
    # Önce weather_all.json'u kontrol et (tüm şehirler birleşik)
    weather_all_file = DATA_DIR / "weather_all.json"
    if weather_all_file.exists():
        return str(weather_all_file)
    
    # Yoksa eski format dosyalarını ara
    pattern = str(DATA_DIR / "weather_*.json")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def load_earthquake_data():
    """Deprem verilerini yükle"""
    file_path = get_latest_earthquake_file()
    if not file_path:
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def load_weather_data():
    """Hava durumu verilerini yükle"""
    file_path = get_latest_weather_file()
    if not file_path:
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Eğer liste değilse listeye çevir
            if not isinstance(data, list):
                return [data]
            # Boş liste kontrolü
            if not data:
                return []
            return data
    except Exception as e:
        print(f"Error loading weather data from {file_path}: {e}")
        return []

def load_forecast_data():
    """Forecast (tahmin) verilerini yükle - Sadece Amerika kıtaları"""
    weather_data = load_weather_data()
    # Sadece forecast tipindeki verileri filtrele
    forecasts = [item for item in weather_data if item.get('type') == 'weather_forecast']
    
    # Amerika kıtaları filtresi: [minLon, minLat, maxLon, maxLat] = [-180, -60, -30, 85]
    americas_bbox = {'min_lon': -180, 'min_lat': -60, 'max_lon': -30, 'max_lat': 85}
    filtered_forecasts = []
    
    for forecast in forecasts:
        lat = forecast.get('latitude')
        lon = forecast.get('longitude')
        
        # Koordinat varsa ve Amerika kıtaları içindeyse ekle
        if lat is not None and lon is not None:
            if (americas_bbox['min_lat'] <= lat <= americas_bbox['max_lat'] and
                americas_bbox['min_lon'] <= lon <= americas_bbox['max_lon']):
                filtered_forecasts.append(forecast)
    
    # Şehirlere göre grupla
    forecasts_by_city = {}
    for forecast in filtered_forecasts:
        city = forecast.get('location', 'Unknown')
        if city not in forecasts_by_city:
            forecasts_by_city[city] = []
        forecasts_by_city[city].append(forecast)
    
    # Her şehir için tarihe göre sırala
    for city in forecasts_by_city:
        forecasts_by_city[city].sort(key=lambda x: x.get('forecast_time', ''))
    
    return forecasts_by_city

def get_current_weather_data():
    """Sadece anlık hava durumu verilerini yükle (forecast hariç) - Sadece Amerika kıtaları"""
    weather_data = load_weather_data()
    # Sadece current weather tipindeki verileri filtrele
    current_weather = [item for item in weather_data if item.get('type') == 'weather']
    
    # Amerika kıtaları filtresi: [minLon, minLat, maxLon, maxLat] = [-180, -60, -30, 85]
    americas_bbox = {'min_lon': -180, 'min_lat': -60, 'max_lon': -30, 'max_lat': 85}
    filtered_weather = []
    
    for item in current_weather:
        lat = item.get('latitude')
        lon = item.get('longitude')
        
        # Koordinat varsa ve Amerika kıtaları içindeyse ekle
        if lat is not None and lon is not None:
            if (americas_bbox['min_lat'] <= lat <= americas_bbox['max_lat'] and
                americas_bbox['min_lon'] <= lon <= americas_bbox['max_lon']):
                filtered_weather.append(item)
        else:
            # Koordinat yoksa atla (sadece Amerika kıtalarına odaklandığımız için)
            pass
    
    return filtered_weather

def calculate_statistics(earthquakes):
    """İstatistikleri hesapla"""
    if not earthquakes:
        return {
            'total': 0,
            'max_mag': 0,
            'min_mag': 0,
            'avg_mag': 0,
            'regions': {}
        }
    
    magnitudes = [eq['magnitude'] for eq in earthquakes]
    
    # Bölgelere göre grupla
    regions = {}
    for eq in earthquakes:
        location = eq['location']
        # Basit bölge çıkarımı
        if 'Alaska' in location:
            region = 'Alaska'
        elif 'California' in location or 'CA' in location:
            region = 'California'
        elif 'Japan' in location:
            region = 'Japan'
        elif 'Chile' in location:
            region = 'Chile'
        elif 'Indonesia' in location:
            region = 'Indonesia'
        elif 'Puerto Rico' in location:
            region = 'Puerto Rico'
        else:
            region = 'Other'
        
        regions[region] = regions.get(region, 0) + 1
    
    return {
        'total': len(earthquakes),
        'max_mag': round(max(magnitudes), 2),
        'min_mag': round(min(magnitudes), 2),
        'avg_mag': round(sum(magnitudes) / len(magnitudes), 2),
        'regions': regions
    }

@app.route('/')
def dashboard():
    """Ana dashboard sayfası"""
    return render_template('dashboard.html')

@app.route('/api/earthquakes')
def api_earthquakes():
    """Deprem verilerini JSON olarak döndür"""
    earthquakes = load_earthquake_data()
    stats = calculate_statistics(earthquakes)
    
    return jsonify({
        'earthquakes': earthquakes,
        'statistics': stats,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/weather')
def api_weather():
    """Hava durumu verilerini JSON olarak döndür (sadece anlık)"""
    weather_data = get_current_weather_data()
    
    return jsonify({
        'weather': weather_data,
        'count': len(weather_data),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/forecast')
def api_forecast():
    """Forecast (tahmin) verilerini JSON olarak döndür"""
    forecasts = load_forecast_data()
    
    return jsonify({
        'forecasts': forecasts,
        'cities': list(forecasts.keys()),
        'count': sum(len(v) for v in forecasts.values()),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/news')
def api_news():
    """Haber başlıklarını JSON olarak döndür"""
    try:
        news = scrape_all_risk_headlines()
        return jsonify({
            'news': news,
            'count': len(news),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'news': [],
            'count': 0,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

def get_latest_event_date(events, event_type=None):
    """Belirli bir event tipinin en yakın tarihini bul"""
    if not events:
        return None
    
    latest_date = None
    for event in events:
        # Event tipi kontrolü (storm, volcano için)
        if event_type:
            if event_type == 'storm':
                # Storm kontrolü
                categories = event.get('categories', [])
                cat_str = ' '.join([str(c) for c in categories]).lower() if isinstance(categories, list) else str(categories).lower()
                if 'storm' not in cat_str and 'severe' not in cat_str:
                    continue
            elif event_type == 'volcano':
                # Volcano kontrolü
                categories = event.get('categories', [])
                cat_str = ' '.join([str(c) for c in categories]).lower() if isinstance(categories, list) else str(categories).lower()
                if 'volcano' not in cat_str:
                    continue
        
        time_str = event.get('event_time') or event.get('time') or event.get('timestamp')
        if not time_str:
            continue
        
        try:
            if 'T' in str(time_str):
                time_str_clean = str(time_str).replace('Z', '+00:00')
                event_time = datetime.fromisoformat(time_str_clean)
            elif ' ' in str(time_str) and 'T' not in str(time_str):
                try:
                    event_time = datetime.strptime(str(time_str), '%Y-%m-%d T%H:%M:%S')
                except:
                    event_time = datetime.strptime(str(time_str), '%Y-%m-%d %H:%M:%S')
            else:
                event_time = datetime.fromtimestamp(float(time_str))
            
            if event_time.tzinfo:
                event_time = event_time.astimezone().replace(tzinfo=None)
            
            if latest_date is None or event_time > latest_date:
                latest_date = event_time
        except:
            continue
    
    return latest_date

def filter_events_from_latest(events, event_type=None):
    """En yakın event tarihinden itibaren tüm event'leri filtrele"""
    if not events:
        return []
    
    # En yakın event tarihini bul
    latest_date = get_latest_event_date(events, event_type)
    
    if latest_date is None:
        # Eğer en yakın tarih bulunamazsa, son 1 hafta filtresi uygula
        return filter_last_one_week(events)
    
    filtered = []
    
    for event in events:
        # Event tipi kontrolü
        if event_type:
            if event_type == 'storm':
                categories = event.get('categories', [])
                cat_str = ' '.join([str(c) for c in categories]).lower() if isinstance(categories, list) else str(categories).lower()
                if 'storm' not in cat_str and 'severe' not in cat_str:
                    continue
            elif event_type == 'volcano':
                categories = event.get('categories', [])
                cat_str = ' '.join([str(c) for c in categories]).lower() if isinstance(categories, list) else str(categories).lower()
                if 'volcano' not in cat_str:
                    continue
        
        time_str = event.get('event_time') or event.get('time') or event.get('timestamp')
        if not time_str:
            continue
        
        try:
            if 'T' in str(time_str):
                time_str_clean = str(time_str).replace('Z', '+00:00')
                event_time = datetime.fromisoformat(time_str_clean)
            elif ' ' in str(time_str) and 'T' not in str(time_str):
                try:
                    event_time = datetime.strptime(str(time_str), '%Y-%m-%d T%H:%M:%S')
                except:
                    event_time = datetime.strptime(str(time_str), '%Y-%m-%d %H:%M:%S')
            else:
                event_time = datetime.fromtimestamp(float(time_str))
            
            if event_time.tzinfo:
                event_time = event_time.astimezone().replace(tzinfo=None)
            
            # En yakın tarihten itibaren tüm event'leri ekle
            if event_time >= latest_date:
                filtered.append(event)
        except Exception as e:
            continue
    
    return filtered

def filter_last_one_week(events):
    """Son 1 hafta içindeki event'leri filtrele"""
    if not events:
        return []
    
    one_week_ago = datetime.now() - timedelta(days=7)
    filtered = []
    
    for event in events:
        # Tarih field'ını bul (time, timestamp, event_time, etc.)
        # Öncelik sırası: event_time > time > timestamp
        # EONET verilerinde event_time gerçek event zamanı, time ise güncelleme zamanı olabilir
        event_time = None
        time_str = event.get('event_time') or event.get('time') or event.get('timestamp')
        
        # Eğer time field'ı yoksa, event'i atla (filtreleme yapamayız)
        if not time_str:
            continue
        
        try:
            # Farklı tarih formatlarını parse et
            if 'T' in str(time_str):
                # ISO format: "2025-12-26T19:00:00+00:00" veya "2025-12-26T19:00:00Z"
                time_str_clean = str(time_str).replace('Z', '+00:00')
                try:
                    event_time = datetime.fromisoformat(time_str_clean)
                except ValueError:
                    # ISO format parse edilemezse, basit format dene
                    try:
                        event_time = datetime.strptime(str(time_str).split('T')[0], '%Y-%m-%d')
                    except:
                        event_time = None
            elif ' ' in str(time_str) and 'T' not in str(time_str):
                # Space format: "2025-12-30 T00:00:00" veya "2025-12-30 00:00:00"
                try:
                    event_time = datetime.strptime(str(time_str), '%Y-%m-%d T%H:%M:%S')
                except:
                    try:
                        event_time = datetime.strptime(str(time_str), '%Y-%m-%d %H:%M:%S')
                    except:
                        event_time = None
            else:
                # Unix timestamp veya diğer formatlar
                try:
                    event_time = datetime.fromtimestamp(float(time_str))
                except:
                    event_time = None
            
            # Eğer tarih parse edilemediyse, event'i atla
            if not event_time:
                continue
            
            # UTC'den local time'a çevir (eğer timezone bilgisi varsa)
            if event_time.tzinfo:
                # Timezone-aware datetime'ı local time'a çevir, sonra naive yap
                event_time = event_time.astimezone().replace(tzinfo=None)
            
            # Son 1 hafta içindeyse ekle
            if event_time >= one_week_ago:
                filtered.append(event)
        except Exception as e:
            # Parse edilemezse event'i atla
            print(f"Tarih parse hatası: {time_str}, {e}")
            continue
    
    return filtered

def load_eonet_data():
    """EONET doğal afet verilerini yükle - Pipeline'dan oluşturulan JSON dosyasından"""
    if not EONET_AVAILABLE:
        return []
    
    # Önce pipeline'dan oluşturulan JSON dosyasını kontrol et
    eonet_file = DATA_DIR / "eonet_events.json"
    if eonet_file.exists():
        try:
            with open(eonet_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Eğer liste değilse listeye çevir
                if not isinstance(data, list):
                    data = [data] if data else []
                
                # Volkan verilerini ayrı filtrele (en yakın volkan tarihinden itibaren)
                volcano_data = filter_events_from_latest(data, event_type='volcano')
                # Diğer veriler için son 1 hafta filtresi
                other_data = filter_last_one_week([e for e in data if not any('volcano' in str(c).lower() for c in (e.get('categories', []) if isinstance(e.get('categories'), list) else [e.get('categories')]))])
                
                # Birleştir
                return volcano_data + other_data
        except Exception as e:
            print(f"EONET JSON dosyası okuma hatası: {e}")
    
    # JSON dosyası yoksa veya okunamazsa, API'den çek (fallback)
    # Not: Pipeline çalıştığında JSON dosyası oluşturulacak
    try:
        # Pipeline'da bbox filtresi zaten uygulanıyor, burada da uygulayalım
        americas_bbox = [-180, -60, -30, 85]
        src = EONETSource(status="open", days=30, limit=100, bbox=americas_bbox)
        events = src.fetch_and_parse()
        events_dict = [e.toDictionary() for e in events]
        # Volkan verilerini ayrı filtrele
        volcano_data = filter_events_from_latest(events_dict, event_type='volcano')
        # Diğer veriler için son 1 hafta filtresi
        other_data = filter_last_one_week([e for e in events_dict if not any('volcano' in str(c).lower() for c in (e.get('categories', []) if isinstance(e.get('categories'), list) else [e.get('categories')]))])
        return volcano_data + other_data
    except Exception as e:
        print(f"EONET veri yükleme hatası: {e}")
        return []

def generate_current_alerts(earthquakes, current_weather_data, eonet_events=None):
    """Mevcut durumdan kaynaklanan alert'ler oluştur (current weather + EONET)"""
    alerts = []
    
    # EONET verileri yoksa yükle
    if eonet_events is None:
        eonet_events = load_eonet_data()
    
    # Deprem alert'leri (magnitude >= 5.0)
    for eq in earthquakes:
        if eq.get('magnitude', 0) >= 5.0:
            alerts.append({
                'type': 'earthquake',
                'category': 'current',
                'severity': 'high' if eq.get('magnitude', 0) >= 6.0 else 'medium',
                'title': f"Yüksek Büyüklükte Deprem: {eq.get('magnitude', 0):.1f}",
                'message': f"{eq.get('location', 'Bilinmeyen')} bölgesinde {eq.get('magnitude', 0):.1f} büyüklüğünde deprem",
                'location': eq.get('location', 'Bilinmeyen'),
                'timestamp': eq.get('timestamp', datetime.now().isoformat()),
                'data': eq
            })
    
    # Mevcut hava durumu alert'leri
    for weather in current_weather_data:
        temp = weather.get('temperature', 0)
        feels_like = weather.get('feels_like', temp)
        temp_max = weather.get('temp_max', temp)
        wind = weather.get('wind_speed', 0)
        wind_gust = weather.get('wind_gust', 0)
        humidity = weather.get('humidity', 0)
        pressure = weather.get('pressure', 0)
        visibility = weather.get('visibility', 0)
        clouds = weather.get('clouds', 0)
        weather_main = weather.get('weather_main', '').lower()
        location = weather.get('location', 'Bilinmeyen')
        
        # Aşırı sıcak (>= 35°C)
        if temp >= 35:
            alerts.append({
                'type': 'weather',
                'category': 'current',
                'severity': 'high',
                'title': f'Aşırı Sıcak Uyarısı: {location}',
                'message': f'{location} şehrinde sıcaklık {temp:.1f}°C (hissedilen: {feels_like:.1f}°C) - Aşırı sıcak hava uyarısı',
                'location': location,
                'timestamp': weather.get('time', datetime.now().isoformat()),
                'data': weather
            })
        
        # Çok sıcak (30-35°C arası)
        elif temp >= 30:
            alerts.append({
                'type': 'weather',
                'category': 'current',
                'severity': 'medium',
                'title': f'Yüksek Sıcaklık Uyarısı: {location}',
                'message': f'{location} şehrinde sıcaklık {temp:.1f}°C - Yüksek sıcaklık uyarısı',
                'location': location,
                'timestamp': weather.get('time', datetime.now().isoformat()),
                'data': weather
            })
        
        # Aşırı soğuk (<= -5°C)
        if temp <= -5:
            alerts.append({
                'type': 'weather',
                'category': 'current',
                'severity': 'high',
                'title': f'Aşırı Soğuk Uyarısı: {location}',
                'message': f'{location} şehrinde sıcaklık {temp:.1f}°C (hissedilen: {feels_like:.1f}°C) - Aşırı soğuk hava uyarısı',
                'location': location,
                'timestamp': weather.get('time', datetime.now().isoformat()),
                'data': weather
            })
        
        # Çok soğuk (0 ile -5°C arası)
        elif temp <= 0:
            alerts.append({
                'type': 'weather',
                'category': 'current',
                'severity': 'medium',
                'title': f'Düşük Sıcaklık Uyarısı: {location}',
                'message': f'{location} şehrinde sıcaklık {temp:.1f}°C - Düşük sıcaklık uyarısı',
                'location': location,
                'timestamp': weather.get('time', datetime.now().isoformat()),
                'data': weather
            })
        
        # Yüksek rüzgar (>= 15 m/s)
        if wind >= 15:
            alerts.append({
                'type': 'weather',
                'severity': 'high' if wind >= 20 else 'medium',
                'title': f'Yüksek Rüzgar Uyarısı: {location}',
                'message': f'{location} şehrinde rüzgar hızı {wind:.1f} m/s' + 
                          (f' (rüzgar fırtınası: {wind_gust:.1f} m/s)' if wind_gust and wind_gust > wind else '') + 
                          ' - Yüksek rüzgar uyarısı',
                'location': location,
                'timestamp': weather.get('time', datetime.now().isoformat()),
                'data': weather
            })
        
        # Güçlü rüzgar (10-15 m/s arası)
        elif wind >= 10:
            alerts.append({
                'type': 'weather',
                'category': 'current',
                'severity': 'medium',
                'title': f'Güçlü Rüzgar Uyarısı: {location}',
                'message': f'{location} şehrinde rüzgar hızı {wind:.1f} m/s - Güçlü rüzgar uyarısı',
                'location': location,
                'timestamp': weather.get('time', datetime.now().isoformat()),
                'data': weather
            })
        
        # Yüksek nem (>= 90%)
        if humidity >= 90:
            alerts.append({
                'type': 'weather',
                'category': 'current',
                'severity': 'medium',
                'title': f'Yüksek Nem Uyarısı: {location}',
                'message': f'{location} şehrinde nem oranı %{humidity:.0f} - Yüksek nem uyarısı (yağış riski)',
                'location': location,
                'timestamp': weather.get('time', datetime.now().isoformat()),
                'data': weather
            })
        
        # Düşük basınç (<= 1000 hPa) - fırtına işareti
        if pressure and pressure <= 1000:
            alerts.append({
                'type': 'weather',
                'category': 'current',
                'severity': 'high',
                'title': f'Düşük Basınç Uyarısı: {location}',
                'message': f'{location} şehrinde atmosfer basıncı {pressure:.0f} hPa - Düşük basınç uyarısı (fırtına riski)',
                'location': location,
                'timestamp': weather.get('time', datetime.now().isoformat()),
                'data': weather
            })
        
        # Düşük görüş mesafesi (<= 1000m) - sis uyarısı
        if visibility and visibility <= 1000:
            alerts.append({
                'type': 'weather',
                'severity': 'high' if visibility <= 500 else 'medium',
                'title': f'Düşük Görüş Mesafesi Uyarısı: {location}',
                'message': f'{location} şehrinde görüş mesafesi {visibility/1000:.1f} km - Düşük görüş uyarısı (sis riski)',
                'location': location,
                'timestamp': weather.get('time', datetime.now().isoformat()),
                'data': weather
            })
        
        # Yağış uyarıları (weather condition'a göre)
        if weather_main in ['rain', 'drizzle', 'thunderstorm']:
            alerts.append({
                'type': 'weather',
                'severity': 'high' if weather_main == 'thunderstorm' else 'medium',
                'title': f'Yağış Uyarısı: {location}',
                'message': f'{location} şehrinde {weather.get("weather_description", "yağış")} bekleniyor - Yağış uyarısı',
                'location': location,
                'timestamp': weather.get('time', datetime.now().isoformat()),
                'data': weather
            })
        
        # Kar uyarısı
        if weather_main == 'snow':
            alerts.append({
                'type': 'weather',
                'category': 'current',
                'severity': 'high',
                'title': f'Kar Uyarısı: {location}',
                'message': f'{location} şehrinde kar yağışı bekleniyor - Kar uyarısı',
                'location': location,
                'timestamp': weather.get('time', datetime.now().isoformat()),
                'data': weather
            })
        
        # Yoğun bulutluluk (>= 80%)
        if clouds >= 80:
            alerts.append({
                'type': 'weather',
                'category': 'current',
                'severity': 'medium',
                'title': f'Yoğun Bulutluluk: {location}',
                'message': f'{location} şehrinde bulutluluk %{clouds:.0f} - Yoğun bulutluluk (yağış riski)',
                'location': location,
                'timestamp': weather.get('time', datetime.now().isoformat()),
                'data': weather
            })
    
    # EONET doğal afet alert'leri (sadece açık olanlar)
    for event in eonet_events:
        if event.get('status') == 'open':
            categories = event.get('categories', [])
            title = event.get('title', 'Doğal Afet')
            event_time = event.get('event_time', event.get('time', datetime.now().isoformat()))
            
            # Kategoriye göre severity belirle
            severity = 'high'  # Varsayılan olarak yüksek öncelik
            category_str = ','.join(categories).lower() if categories else ''
            
            # Yangın ve volkan için yüksek öncelik
            if 'wildfire' in category_str or 'fire' in category_str or 'yangın' in category_str:
                severity = 'high'
            elif 'volcano' in category_str or 'volkan' in category_str:
                severity = 'high'
            elif 'storm' in category_str or 'fırtına' in category_str or 'severe' in category_str:
                severity = 'high'
            elif 'flood' in category_str or 'sel' in category_str:
                severity = 'high'
            else:
                severity = 'medium'
            
            # Konum bilgisi
            location = 'Bilinmeyen Konum'
            if event.get('latitude') and event.get('longitude'):
                location = f"Koordinat: {event.get('latitude'):.4f}, {event.get('longitude'):.4f}"
            
            # Kategori metni
            category_text = ', '.join(categories) if categories else 'Doğal Afet'
            
            alerts.append({
                'type': 'natural_event',
                'category': 'current',
                'severity': severity,
                'title': f'Doğal Afet Uyarısı: {title}',
                'message': f'{category_text} - {title}. Durum: AÇIK. {location}',
                'location': location,
                'timestamp': event_time,
                'data': event
            })
    
    # Tarihe göre sırala (en yeni önce)
    alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return alerts

def generate_forecast_alerts(forecasts_by_city):
    """Forecast verilerinden alert'ler oluştur (ileriye dönük uyarılar)
    
    Aynı şehir için aynı tip uyarıları birleştirir (tekrar eden uyarıları önler).
    """
    alerts = []
    
    for city, forecast_list in forecasts_by_city.items():
        if not forecast_list:
            continue
        
        # Şehir için kritik durumları tespit et
        low_temps = []
        high_temps = []
        high_winds = []
        snow_forecasts = []
        rain_forecasts = []
        high_humidity = []
        low_pressure = []
        
        for forecast in forecast_list:
            temp = forecast.get('temperature', 0)
            wind = forecast.get('wind_speed', 0)
            humidity = forecast.get('humidity', 0)
            pressure = forecast.get('pressure', 0)
            weather_main = forecast.get('weather_main', '').lower()
            forecast_time = forecast.get('forecast_time', '')
            
            # Düşük sıcaklık (<= 0°C)
            if temp <= 0:
                low_temps.append({'temp': temp, 'time': forecast_time})
            
            # Yüksek sıcaklık (>= 30°C)
            if temp >= 30:
                high_temps.append({'temp': temp, 'time': forecast_time})
            
            # Yüksek rüzgar (>= 15 m/s)
            if wind >= 15:
                high_winds.append({'wind': wind, 'time': forecast_time})
            
            # Kar yağışı
            if weather_main == 'snow':
                snow_forecasts.append({'time': forecast_time})
            
            # Yağış
            if weather_main in ['rain', 'drizzle', 'thunderstorm']:
                rain_forecasts.append({'type': weather_main, 'time': forecast_time})
            
            # Yüksek nem (>= 90%)
            if humidity >= 90:
                high_humidity.append({'humidity': humidity, 'time': forecast_time})
            
            # Düşük basınç (<= 1000 hPa)
            if pressure and pressure <= 1000:
                low_pressure.append({'pressure': pressure, 'time': forecast_time})
        
        # Birleştirilmiş uyarılar oluştur
        if low_temps:
            min_temp = min(t['temp'] for t in low_temps)
            max_temp = max(t['temp'] for t in low_temps)
            count = len(low_temps)
            alerts.append({
                'type': 'weather',
                'category': 'forecast',
                'severity': 'high' if min_temp <= -5 else 'medium',
                'title': f'Düşük Sıcaklık Tahmini: {city}',
                'message': f'{city} şehrinde önümüzdeki 5 günde {count} tahmin noktasında düşük sıcaklık bekleniyor ({min_temp:.1f}°C ile {max_temp:.1f}°C arası)',
                'location': city,
                'timestamp': low_temps[0]['time'],
                'data': {'forecast_count': count, 'min_temp': min_temp, 'max_temp': max_temp}
            })
        
        if high_temps:
            min_temp = min(t['temp'] for t in high_temps)
            max_temp = max(t['temp'] for t in high_temps)
            count = len(high_temps)
            alerts.append({
                'type': 'weather',
                'category': 'forecast',
                'severity': 'high' if max_temp >= 35 else 'medium',
                'title': f'Yüksek Sıcaklık Tahmini: {city}',
                'message': f'{city} şehrinde önümüzdeki 5 günde {count} tahmin noktasında yüksek sıcaklık bekleniyor ({min_temp:.1f}°C ile {max_temp:.1f}°C arası)',
                'location': city,
                'timestamp': high_temps[0]['time'],
                'data': {'forecast_count': count, 'min_temp': min_temp, 'max_temp': max_temp}
            })
        
        if high_winds:
            max_wind = max(w['wind'] for w in high_winds)
            count = len(high_winds)
            alerts.append({
                'type': 'weather',
                'category': 'forecast',
                'severity': 'high' if max_wind >= 20 else 'medium',
                'title': f'Yüksek Rüzgar Tahmini: {city}',
                'message': f'{city} şehrinde önümüzdeki 5 günde {count} tahmin noktasında yüksek rüzgar bekleniyor (maksimum: {max_wind:.1f} m/s)',
                'location': city,
                'timestamp': high_winds[0]['time'],
                'data': {'forecast_count': count, 'max_wind': max_wind}
            })
        
        if snow_forecasts:
            alerts.append({
                'type': 'weather',
                'category': 'forecast',
                'severity': 'high',
                'title': f'Kar Yağışı Tahmini: {city}',
                'message': f'{city} şehrinde önümüzdeki 5 günde kar yağışı bekleniyor',
                'location': city,
                'timestamp': snow_forecasts[0]['time'],
                'data': {'forecast_count': len(snow_forecasts)}
            })
        
        if rain_forecasts:
            thunderstorm_count = sum(1 for r in rain_forecasts if r['type'] == 'thunderstorm')
            severity = 'high' if thunderstorm_count > 0 else 'medium'
            alert_type = 'Fırtına' if thunderstorm_count > 0 else 'Yağış'
            alerts.append({
                'type': 'weather',
                'category': 'forecast',
                'severity': severity,
                'title': f'{alert_type} Tahmini: {city}',
                'message': f'{city} şehrinde önümüzdeki 5 günde {len(rain_forecasts)} tahmin noktasında yağış bekleniyor' + 
                          (f' ({thunderstorm_count} fırtına tahmini)' if thunderstorm_count > 0 else ''),
                'location': city,
                'timestamp': rain_forecasts[0]['time'],
                'data': {'forecast_count': len(rain_forecasts), 'thunderstorm_count': thunderstorm_count}
            })
        
        if high_humidity:
            max_humidity = max(h['humidity'] for h in high_humidity)
            alerts.append({
                'type': 'weather',
                'category': 'forecast',
                'severity': 'medium',
                'title': f'Yüksek Nem Tahmini: {city}',
                'message': f'{city} şehrinde önümüzdeki 5 günde {len(high_humidity)} tahmin noktasında yüksek nem bekleniyor (maksimum: %{max_humidity:.0f})',
                'location': city,
                'timestamp': high_humidity[0]['time'],
                'data': {'forecast_count': len(high_humidity), 'max_humidity': max_humidity}
            })
        
        if low_pressure:
            min_pressure = min(p['pressure'] for p in low_pressure)
            alerts.append({
                'type': 'weather',
                'category': 'forecast',
                'severity': 'high',
                'title': f'Düşük Basınç Tahmini: {city}',
                'message': f'{city} şehrinde önümüzdeki 5 günde {len(low_pressure)} tahmin noktasında düşük basınç bekleniyor (minimum: {min_pressure:.0f} hPa) - Fırtına riski',
                'location': city,
                'timestamp': low_pressure[0]['time'],
                'data': {'forecast_count': len(low_pressure), 'min_pressure': min_pressure}
            })
    
    # Tarihe göre sırala (en yeni önce)
    alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return alerts

@app.route('/api/alerts')
def api_alerts():
    """Tüm alert'leri JSON olarak döndür (current + forecast)"""
    earthquakes = load_earthquake_data()
    current_weather = get_current_weather_data()
    eonet_events = load_eonet_data()
    forecasts = load_forecast_data()
    
    current_alerts = generate_current_alerts(earthquakes, current_weather, eonet_events)
    forecast_alerts = generate_forecast_alerts(forecasts)
    
    all_alerts = current_alerts + forecast_alerts
    
    return jsonify({
        'alerts': all_alerts,
        'current': current_alerts,
        'forecast': forecast_alerts,
        'count': len(all_alerts),
        'current_count': len(current_alerts),
        'forecast_count': len(forecast_alerts),
        'high_severity': len([a for a in all_alerts if a.get('severity') == 'high']),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/alerts/current')
def api_alerts_current():
    """Sadece mevcut durumdan kaynaklanan alert'leri döndür"""
    earthquakes = load_earthquake_data()
    current_weather = get_current_weather_data()
    eonet_events = load_eonet_data()
    alerts = generate_current_alerts(earthquakes, current_weather, eonet_events)
    
    return jsonify({
        'alerts': alerts,
        'count': len(alerts),
        'high_severity': len([a for a in alerts if a.get('severity') == 'high']),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/alerts/forecast')
def api_alerts_forecast():
    """Sadece forecast'ten kaynaklanan alert'leri döndür"""
    forecasts = load_forecast_data()
    alerts = generate_forecast_alerts(forecasts)
    
    return jsonify({
        'alerts': alerts,
        'count': len(alerts),
        'high_severity': len([a for a in alerts if a.get('severity') == 'high']),
        'timestamp': datetime.now().isoformat()
    })

def load_wildfire_data():
    """Wildfire verilerini yükle - Son 1 hafta filtresi uygula"""
    wildfire_file = DATA_DIR / "wildfires.json"
    if not wildfire_file.exists():
        return []
    
    try:
        with open(wildfire_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Eğer liste değilse listeye çevir
            if not isinstance(data, list):
                data = [data] if data else []
            
            # Son 1 hafta filtresi uygula
            return filter_last_one_week(data)
    except Exception as e:
        print(f"Error loading wildfire data: {e}")
        return []

def load_storm_data():
    """Storm verilerini yükle - En yakın fırtına tarihinden itibaren filtrele"""
    storm_file = DATA_DIR / "storms.json"
    if not storm_file.exists():
        return []
    
    try:
        with open(storm_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Eğer liste değilse listeye çevir
            if not isinstance(data, list):
                data = [data] if data else []
            
            # En yakın fırtına tarihinden itibaren filtrele
            return filter_events_from_latest(data, event_type='storm')
    except Exception as e:
        print(f"Error loading storm data: {e}")
        return []

def load_volcano_data():
    """Volcano verilerini yükle - En yakın volkan tarihinden itibaren filtrele"""
    volcano_file = DATA_DIR / "volcanoes.json"
    if not volcano_file.exists():
        return []
    
    try:
        with open(volcano_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Eğer liste değilse listeye çevir
            if not isinstance(data, list):
                data = [data] if data else []
            
            # En yakın volkan tarihinden itibaren filtrele
            return filter_events_from_latest(data, event_type='volcano')
    except Exception as e:
        print(f"Error loading volcano data: {e}")
        return []

def load_flood_data():
    """Flood risk verilerini yükle - Son 1 hafta filtresi uygula (tüm risk seviyeleri dahil)
    Efe'nin flood_regional_analysis modülünü kullanarak veri yükleme"""
    from processing.flood_regional_analysis import load_flood_data as load_flood_data_analysis
    
    # Efe'nin modülünü kullanarak veriyi yükle
    payload = load_flood_data_analysis()
    if payload is None:
        return []
    
    # Flood risk JSON'u object formatında, events array'ini döndür
    if isinstance(payload, dict):
        events = payload.get("events", [])
    else:
        events = payload if isinstance(payload, list) else []
    
    # Flood verilerindeki tarih formatı: "2025-12-30 T00:00:00" - özel parse gerekli
    # Son 1 hafta filtresi uygula (tüm risk seviyeleri dahil)
    one_week_ago = datetime.now() - timedelta(days=7)
    filtered = []
    
    for event in events:
        time_str = event.get('time')
        if not time_str:
            continue
        
        try:
            # Flood verilerindeki özel format: "2025-12-30 T00:00:00"
            if ' T' in str(time_str):
                event_time = datetime.strptime(str(time_str), '%Y-%m-%d T%H:%M:%S')
            elif 'T' in str(time_str):
                time_str_clean = str(time_str).replace('Z', '+00:00')
                event_time = datetime.fromisoformat(time_str_clean)
            else:
                event_time = datetime.strptime(str(time_str), '%Y-%m-%d %H:%M:%S')
            
            if event_time.tzinfo:
                event_time = event_time.astimezone().replace(tzinfo=None)
            
            if event_time >= one_week_ago:
                filtered.append(event)
        except Exception as e:
            print(f"Flood tarih parse hatası: {time_str}, {e}")
            continue
    
    return filtered

@app.route('/api/wildfires')
def api_wildfires():
    """Wildfire verilerini döndür"""
    wildfires = load_wildfire_data()
    return jsonify({
        'wildfires': wildfires,
        'count': len(wildfires),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/storms')
def api_storms():
    """Storm verilerini döndür"""
    storms = load_storm_data()
    return jsonify({
        'storms': storms,
        'count': len(storms),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/volcanoes')
def api_volcanoes():
    """Volcano verilerini döndür"""
    volcanoes = load_volcano_data()
    return jsonify({
        'volcanoes': volcanoes,
        'count': len(volcanoes),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/floods')
def api_floods():
    """Flood risk verilerini döndür - Tüm risk seviyeleri (low, medium, high)"""
    floods = load_flood_data()
    # Tüm risk seviyelerini döndür (low, medium, high)
    # Kullanıcı dashboard'da filtreleyebilir
    return jsonify({
        'floods': floods,
        'count': len(floods),
        'high_risk_count': len([f for f in floods if f.get('risk_level') == 'high']),
        'medium_risk_count': len([f for f in floods if f.get('risk_level') == 'medium']),
        'low_risk_count': len([f for f in floods if f.get('risk_level') == 'low']),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/seismic-risk/faults')
def api_seismic_risk_faults():
    """Tüm fay hatlarının listesini döndür"""
    try:
        analyzer = SeismicRiskAnalyzer()
        fault_lines = analyzer.get_all_fault_lines()
        # Bbox bilgisini de ekle
        for fault in fault_lines:
            fault_id = fault['fault_id']
            if fault_id in analyzer.fault_lines:
                fault['bbox'] = analyzer.fault_lines[fault_id]['bbox']
        return jsonify({
            'fault_lines': fault_lines,
            'count': len(fault_lines),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/seismic-risk/fault/<fault_id>')
def api_seismic_risk_fault(fault_id):
    """Belirli bir fay hattı için sismik risk analizi"""
    try:
        result = analyze_seismic_risk(fault_id=fault_id)
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/seismic-risk/region')
def api_seismic_risk_region():
    """Belirli bir bölge için sismik risk analizi"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', default=100, type=float)
        
        if lat is None or lon is None:
            return jsonify({
                "error": "lat ve lon parametreleri gerekli",
                "example": "/api/seismic-risk/region?lat=37.7749&lon=-122.4194&radius=100"
            }), 400
        
        result = analyze_seismic_risk(latitude=lat, longitude=lon, radius_km=radius)
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/seismic-risk/swarms')
def api_seismic_risk_swarms():
    """Deprem sürülerini (swarm) tespit et - birbirine yakın küçük depremler
    Sadece haritada gösterilen (dashboard'dan gelen) deprem verilerini kullanır
    Son 1 gün içindeki depremleri analiz eder (USGS'ten çekilen verilerle uyumlu)"""
    try:
        min_count = request.args.get('min_count', default=3, type=int)
        max_magnitude = request.args.get('max_magnitude', default=5.0, type=float)
        cluster_radius = request.args.get('cluster_radius', default=100, type=float)
        min_days = request.args.get('min_days', default=0, type=int)
        max_days = request.args.get('max_days', default=1, type=int)
        
        # Haritada gösterilen deprem verilerini al (dashboard'dan)
        earthquakes = load_earthquake_data()
        
        # Eğer deprem verisi yoksa boş liste döndür
        if not earthquakes:
            return jsonify({
                'swarms': [],
                'count': 0,
                'parameters': {
                    'min_count': min_count,
                    'max_magnitude': max_magnitude,
                    'cluster_radius_km': cluster_radius,
                    'min_days': min_days,
                    'max_days': max_days
                },
                'timestamp': datetime.now().isoformat(),
                'message': 'Haritada gösterilen deprem verisi bulunamadı'
            })
        
        analyzer = SeismicRiskAnalyzer()
        # Haritada gösterilen deprem verilerini kullanarak swarm tespiti yap
        swarms = analyzer.detect_earthquake_swarms_from_data(
            earthquakes=earthquakes,
            min_count=min_count,
            max_magnitude=max_magnitude,
            cluster_radius_km=cluster_radius,
            min_days=min_days,
            max_days=max_days
        )
        
        return jsonify({
            'swarms': swarms,
            'count': len(swarms),
            'parameters': {
                'min_count': min_count,
                'max_magnitude': max_magnitude,
                'cluster_radius_km': cluster_radius,
                'min_days': min_days,
                'max_days': max_days
            },
            'earthquakes_analyzed': len(earthquakes),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/eonet')
def api_eonet():
    """NASA EONET doğal afet verilerini döndür - Pipeline'dan oluşturulan JSON dosyasından veya API'den"""
    if not EONET_AVAILABLE:
        return jsonify({"error": "EONET module not available"}), 500
    
    # Önce pipeline'dan oluşturulan JSON dosyasını kontrol et
    eonet_file = DATA_DIR / "eonet_events.json"
    if eonet_file.exists():
        try:
            with open(eonet_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Eğer liste değilse listeye çevir
                if not isinstance(data, list):
                    return jsonify([data] if data else [])
                return jsonify(data)
        except Exception as e:
            print(f"EONET JSON dosyası okuma hatası: {e}")
    
    # JSON dosyası yoksa veya okunamazsa, API'den çek (fallback)
    # Varsayılan olarak Amerika kıtaları filtresi uygulanır (pipeline ile tutarlılık için)
    try:
        status = request.args.get("status", "open")
        days = int(request.args.get("days", 30))
        limit = int(request.args.get("limit", 100))

        categories_str = request.args.get("categories", "")
        category_ids = [c.strip() for c in categories_str.split(",") if c.strip()]

        bbox_str = request.args.get("bbox", "")
        bbox = None
        if bbox_str:
            parts = [p.strip() for p in bbox_str.split(",")]
            if len(parts) == 4:
                bbox = [float(x) for x in parts]
        else:
            # Bbox verilmezse, varsayılan olarak Amerika kıtaları filtresini uygula
            # Pipeline ile tutarlılık için
            bbox = [-180, -60, -30, 85]

        src = EONETSource(status=status, days=days, limit=limit, category_ids=category_ids, bbox=bbox)
        events = src.fetch_and_parse()
        
        # Iceberg kategorilerini filtrele (pipeline ile tutarlılık için)
        filtered_events = []
        for event in events:
            event_dict = event.toDictionary() if hasattr(event, 'toDictionary') else event
            categories = event_dict.get('categories', [])
            if categories:
                categories_str = ','.join(categories).lower()
                if 'ice' in categories_str or 'iceberg' in categories_str or 'sea and lake ice' in categories_str:
                    continue
            filtered_events.append(event)
        
        return jsonify([e.toDictionary() if hasattr(e, 'toDictionary') else e for e in filtered_events])
    except Exception as e:
        import traceback
        print(f"EONET API Error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/seismic-simulation/trigger', methods=['POST'])
def api_seismic_simulation_trigger():
    """Sismik Acil Durum Operatörü - Deprem simülasyonu başlat
    Kullanıcı tarafından seçilen veya rastgele üretilen deprem için erken uyarı hesaplamaları yapar"""
    from processing.seismic_simulation import simulate_earthquake
    
    try:
        data = request.get_json() or {}
        user_lat = data.get('user_latitude')
        user_lon = data.get('user_longitude')
        epicenter_lat = data.get('epicenter_latitude')
        epicenter_lon = data.get('epicenter_longitude')
        
        # Simülasyonu çalıştır
        result = simulate_earthquake(
            user_lat=user_lat,
            user_lon=user_lon,
            epicenter_lat=epicenter_lat,
            epicenter_lon=epicenter_lon
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Başlangıçta eski dosyaları temizle
    try:
        cleanup_old_files()
    except Exception as e:
        print(f"Temizleme hatası (devam ediliyor): {e}")
    
    print("\n" + "="*60)
    print("  🌍 SDEWS WEB DASHBOARD")
    print("="*60)
    print("\n  📍 Tarayıcıda şu adresi aç:")
    print("     http://localhost:5000")
    print("\n  ⚠️  Durdurmak için: Ctrl+C")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

