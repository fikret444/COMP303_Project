"""
SDEWS Web Dashboard
Tarayıcıda görsel deprem takip sistemi
"""

from flask import Flask, render_template, jsonify
import json
import os
import glob
from datetime import datetime
from pathlib import Path
from datasources.scraping.scrape_news import scrape_all_risk_headlines

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
    """Forecast (tahmin) verilerini yükle"""
    weather_data = load_weather_data()
    # Sadece forecast tipindeki verileri filtrele
    forecasts = [item for item in weather_data if item.get('type') == 'weather_forecast']
    
    # Şehirlere göre grupla
    forecasts_by_city = {}
    for forecast in forecasts:
        city = forecast.get('location', 'Unknown')
        if city not in forecasts_by_city:
            forecasts_by_city[city] = []
        forecasts_by_city[city].append(forecast)
    
    # Her şehir için tarihe göre sırala
    for city in forecasts_by_city:
        forecasts_by_city[city].sort(key=lambda x: x.get('forecast_time', ''))
    
    return forecasts_by_city

def get_current_weather_data():
    """Sadece anlık hava durumu verilerini yükle (forecast hariç)"""
    weather_data = load_weather_data()
    # Sadece current weather tipindeki verileri filtrele
    return [item for item in weather_data if item.get('type') == 'weather']

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

@app.route('/api/forecast/<city>')
def api_forecast_city(city):
    """Belirli bir şehir için forecast verilerini döndür"""
    forecasts = load_forecast_data()
    city_forecasts = forecasts.get(city, [])
    
    return jsonify({
        'city': city,
        'forecasts': city_forecasts,
        'count': len(city_forecasts),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/all')
def api_all():
    """Tüm verileri (deprem + hava durumu + forecast) JSON olarak döndür"""
    earthquakes = load_earthquake_data()
    weather_data = get_current_weather_data()
    forecasts = load_forecast_data()
    stats = calculate_statistics(earthquakes)
    
    return jsonify({
        'earthquakes': earthquakes,
        'weather': weather_data,
        'forecasts': forecasts,
        'statistics': stats,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/statistics')
def api_statistics():
    """Sadece istatistikleri döndür"""
    earthquakes = load_earthquake_data()
    stats = calculate_statistics(earthquakes)
    return jsonify(stats)

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

def generate_current_alerts(earthquakes, current_weather_data):
    """Mevcut durumdan kaynaklanan alert'ler oluştur (current weather)"""
    alerts = []
    
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
    forecasts = load_forecast_data()
    
    current_alerts = generate_current_alerts(earthquakes, current_weather)
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
    alerts = generate_current_alerts(earthquakes, current_weather)
    
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

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  🌍 SDEWS WEB DASHBOARD")
    print("="*60)
    print("\n  📍 Tarayıcıda şu adresi aç:")
    print("     http://localhost:5000")
    print("\n  ⚠️  Durdurmak için: Ctrl+C")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

