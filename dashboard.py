"""
SDEWS Web Dashboard
Tarayıcıda görsel deprem takip sistemi
"""

from flask import Flask, render_template, jsonify
import json
import os
import glob
from datetime import datetime

app = Flask(__name__)

def get_latest_earthquake_file():
    """En son oluşturulan deprem dosyasını bul"""
    files = glob.glob('data/earthquakes_*.json')
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

@app.route('/api/statistics')
def api_statistics():
    """Sadece istatistikleri döndür"""
    earthquakes = load_earthquake_data()
    stats = calculate_statistics(earthquakes)
    return jsonify(stats)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  🌍 SDEWS WEB DASHBOARD")
    print("="*60)
    print("\n  📍 Tarayıcıda şu adresi aç:")
    print("     http://localhost:5000")
    print("\n  ⚠️  Durdurmak için: Ctrl+C")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

