import requests

# EONET kategorilerini kontrol et
r = requests.get('https://eonet.gsfc.nasa.gov/api/v3/categories')
cats = r.json()

print("EONET API Kategorileri:")
print("=" * 50)
for cat in cats.get('categories', []):
    print(f"{cat['id']}: {cat['title']}")

print("\n" + "=" * 50)
print("\nAçık olayları kontrol ediyorum...")

# Açık olayları kontrol et
r2 = requests.get('https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days=30&limit=100')
events_data = r2.json()

categories_count = {}
for event in events_data.get('events', []):
    for cat in event.get('categories', []):
        cat_title = cat.get('title', '')
        categories_count[cat_title] = categories_count.get(cat_title, 0) + 1

print("\nAçık olayların kategori dağılımı:")
print("=" * 50)
for cat, count in sorted(categories_count.items(), key=lambda x: x[1], reverse=True):
    print(f"{cat}: {count} olay")

# Sel, kuraklık ve kar kontrolü
flood_keywords = ['flood', 'sel']
drought_keywords = ['drought', 'kuraklık']
snow_keywords = ['snow', 'kar']

flood_events = []
drought_events = []
snow_events = []

for event in events_data.get('events', []):
    event_cats = [c.get('title', '').lower() for c in event.get('categories', [])]
    event_cats_str = ' '.join(event_cats)
    
    if any(kw in event_cats_str for kw in flood_keywords):
        flood_events.append(event)
    if any(kw in event_cats_str for kw in drought_keywords):
        drought_events.append(event)
    if any(kw in event_cats_str for kw in snow_keywords):
        snow_events.append(event)

print("\n" + "=" * 50)
print(f"Sel olayları: {len(flood_events)}")
print(f"Kuraklık olayları: {len(drought_events)}")
print(f"Kar olayları: {len(snow_events)}")

if len(flood_events) == 0 and len(drought_events) == 0 and len(snow_events) == 0:
    print("\n⚠️  Bu kategorilerde şu anda açık (open) durumda olay yok.")
    print("Bu normal bir durum - EONET sadece aktif/raporlanan olayları gösterir.")

