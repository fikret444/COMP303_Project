from __future__ import annotations

import requests
import os
from datetime import datetime
from typing import List

from datasources.base_source import DataSource, DataSourceError

# --------------------------------------------------
# TOP 100 CITIES IN THE AMERICAS (population-based)
# --------------------------------------------------

AMERICAS_CITIES = [
    # --- TOP 1–10 ---
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

    # --- 11–20 ---
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

    # --- 21–30 ---
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

    # --- 31–40 ---
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

    # --- 41–50 ---
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

    # --- 51–60 ---
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

    # --- 61–70 ---
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

    # --- 71–80 ---
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

    # --- 81–90 ---
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

    # --- 91–100 ---
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

# --------------------------------------------------
# OpenWeather Source
# --------------------------------------------------

class OpenWeatherSource(DataSource):
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise DataSourceError(
                "OPENWEATHER_API_KEY not found in environment variables."
            )

    def fetch_raw(self):
        results = []

        for city, country in AMERICAS_CITIES:
            params = {
                "q": f"{city},{country}",
                "appid": self.api_key,
                "units": "metric",
            }

            try:
                r = requests.get(self.BASE_URL, params=params, timeout=10)
                r.raise_for_status()
                results.append(r.json())
            except Exception:
                # Skip city if API fails (rate limit, typo, etc.)
                continue

        return results

    def parse(self, raw_list) -> List[dict]:
        events = []

        for raw in raw_list:
            main = raw.get("main", {})
            wind = raw.get("wind", {})
            coord = raw.get("coord", {})
            name = raw.get("name")

            events.append({
                "type": "weather",
                "source": "OpenWeatherMap",
                "location": name,
                "temperature": main.get("temp"),
                "humidity": main.get("humidity"),
                "wind_speed": wind.get("speed"),
                "pressure": main.get("pressure"),
                "time": datetime.utcnow().isoformat(),
                "latitude": coord.get("lat"),
                "longitude": coord.get("lon"),
            })

        return events
