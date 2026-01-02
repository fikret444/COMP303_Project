import os
import requests
from datetime import datetime
from datasources.base_source import DataSource, DataSourceError


# Top 100 cities in the Americas (city, country_code)
AMERICAS_CITIES = [
    ("São Paulo", "BR"),
    ("Lima", "PE"),
    ("Mexico City", "MX"),
    ("New York", "US"),
    ("Bogotá", "CO"),
    ("Rio de Janeiro", "BR"),
    ("Santiago", "CL"),
    ("Los Angeles", "US"),
    ("Buenos Aires", "AR"),
    ("Toronto", "CA"),
    ("Brasília", "BR"),
    ("Salvador", "BR"),
    ("Chicago", "US"),
    ("Fortaleza", "BR"),
    ("Santo Domingo", "DO"),
    ("Belo Horizonte", "BR"),
    ("Medellín", "CO"),
    ("Cali", "CO"),
    ("Houston", "US"),
    ("Guayaquil", "EC"),
    ("Manaus", "BR"),
    ("Havana", "CU"),
    ("Caracas", "VE"),
    ("Curitiba", "BR"),
    ("Ecatepec", "MX"),
    ("Maracaibo", "VE"),
    ("Montreal", "CA"),
    ("Phoenix", "US"),
    ("Recife", "BR"),
    ("Quito", "EC"),
    ("Philadelphia", "US"),
    ("Puebla", "MX"),
    ("Guadalajara", "MX"),
    ("San Antonio", "US"),
    ("Goiânia", "BR"),
    ("Porto Alegre", "BR"),
    ("Belém", "BR"),
    ("Ciudad Juárez", "MX"),
    ("Córdoba", "AR"),
    ("Tijuana", "MX"),
    ("Santa Cruz", "BO"),
    ("San Diego", "US"),
    ("Guarulhos", "BR"),
    ("Dallas", "US"),
    ("Montevideo", "UY"),
    ("León", "MX"),
    ("Rosario", "AR"),
    ("Zapopan", "MX"),
    ("Calgary", "CA"),
    ("Monterrey", "MX"),
    ("Barranquilla", "CO"),
    ("Nezahualcóyotl", "MX"),
    ("Campinas", "BR"),
    ("Barquisimeto", "VE"),
    ("São Gonçalo", "BR"),
    ("Tegucigalpa", "HN"),
    ("São Luís", "BR"),
    ("Managua", "NI"),
    ("San Jose", "US"),
    ("Maceió", "BR"),
    ("Arequipa", "PE"),
    ("Naucalpan", "MX"),
    ("Cartagena", "CO"),
    ("Austin", "US"),
    ("Valencia", "VE"),
    ("Ottawa", "CA"),
    ("Chihuahua", "MX"),
    ("Edmonton", "CA"),
    ("Guatemala City", "GT"),
    ("Duque de Caxias", "BR"),
    ("Jacksonville", "US"),
    ("Fort Worth", "US"),
    ("Ciudad Guayana", "VE"),
    ("Columbus", "US"),
    ("Natal", "BR"),
    ("Campo Grande", "BR"),
    ("San Francisco", "US"),
    ("Port-au-Prince", "HT"),
    ("Charlotte", "US"),
    ("Mérida", "MX"),
    ("Indianapolis", "US"),
    ("Trujillo", "PE"),
    ("El Alto", "BO"),
    ("Hermosillo", "MX"),
    ("Cancún", "MX"),
    ("São Bernardo do Campo", "BR"),
    ("Teresina", "BR"),
    ("Nova Iguaçu", "BR"),
    ("Saltillo", "MX"),
    ("João Pessoa", "BR"),
    ("Aguascalientes", "MX"),
    ("Culiacán", "MX"),
    ("San Luis Potosí", "MX"),
    ("La Paz", "BO"),
    ("Mexicali", "MX"),
    ("Chimalhuacán", "MX"),
    ("Seattle", "US"),
    ("Guadalupe", "MX"),
    ("Acapulco", "MX"),
    ("Mississauga", "CA"),
]


class OpenWeatherSource(DataSource):
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise DataSourceError("Missing OpenWeather API key. Set OPENWEATHER_API_KEY env var.")

    def fetch_raw(self):
        url = "https://api.openweathermap.org/data/2.5/weather"
        results = []

        for city, cc in AMERICAS_CITIES:
            params = {"q": f"{city},{cc}", "appid": self.api_key, "units": "metric"}
            try:
                r = requests.get(url, params=params, timeout=10)
                r.raise_for_status()
                results.append(r.json())
            except Exception:
                # skip failed city
                continue

        return results

    def parse(self, raw_list):
        events = []
        for raw in raw_list:
            main = raw.get("main", {})
            wind = raw.get("wind", {})
            coord = raw.get("coord", {})
            city_name = raw.get("name", "Unknown")

            events.append({
                "type": "weather",
                "source": "OpenWeatherMap",
                "location": city_name,
                "temperature": main.get("temp"),
                "wind_speed": wind.get("speed"),
                "humidity": main.get("humidity"),
                "time": datetime.utcnow().isoformat(),
                "latitude": coord.get("lat"),
                "longitude": coord.get("lon")
            })

        return events


def get_weather_americas():
    src = OpenWeatherSource()
    return src.fetch_and_parse()


if __name__ == "__main__":
    data = get_weather_americas()
    print(f"Collected weather for {len(data)} cities")
    print(data[:3])
