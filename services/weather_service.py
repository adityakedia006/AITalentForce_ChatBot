import httpx
import difflib
from typing import Dict, Tuple


class WeatherService:
    
    def __init__(self):
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"
        self.weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }

        self._common_corrections = {
            "tokoyo": "Tokyo",
            "kyouto": "Kyoto",
            "osaka-shi": "Osaka",
            "newyork": "New York",
        }

        self._fuzzy_candidates = [
            "Tokyo", "Osaka", "Kyoto", "Sapporo", "Nagoya", "Fukuoka", "Yokohama",
            "Paris", "London", "New York", "Delhi", "Mumbai",
            "東京", "大阪", "京都", "札幌", "名古屋", "福岡", "横浜"
        ]
    
    async def get_coordinates(self, location: str) -> Tuple[float, float, str]:
        try:
            is_japanese = any(
                ('\u3040' <= ch <= '\u309F') or ('\u30A0' <= ch <= '\u30FF') or ('\u4E00' <= ch <= '\u9FFF')
                for ch in location
            )
            lang = "ja" if is_japanese else "en"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.geocoding_url,
                    params={"name": location, "count": 1, "language": lang, "format": "json"}
                )
                response.raise_for_status()
                data = response.json()
                
                if not data.get("results"):
                    corrected = self._common_corrections.get(location.strip().lower())
                    if not corrected:
                        best = difflib.get_close_matches(location, self._fuzzy_candidates, n=1, cutoff=0.75)
                        corrected = best[0] if best else None
                    if corrected:
                        response = await client.get(
                            self.geocoding_url,
                            params={"name": corrected, "count": 1, "language": lang, "format": "json"}
                        )
                        response.raise_for_status()
                        data = response.json()
                
                if not data.get("results"):
                    raise ValueError(f"Location '{location}' not found")
                
                result = data["results"][0]
                latitude = result["latitude"]
                longitude = result["longitude"]
                location_name = result["name"]
                
                if "country" in result:
                    location_name = f"{location_name}, {result['country']}"
                
                return latitude, longitude, location_name
                
        except httpx.HTTPError as e:
            raise Exception(f"Geocoding API request failed: {str(e)}")
        except (KeyError, IndexError, ValueError) as e:
            raise Exception(f"Failed to parse geocoding response: {str(e)}")
    
    async def get_weather(self, location: str) -> Dict[str, any]:
        try:
            latitude, longitude, location_name = await self.get_coordinates(location)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.weather_url,
                    params={
                        "latitude": latitude,
                        "longitude": longitude,
                        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                        "timezone": "auto"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                current = data.get("current", {})
                
                weather_code = current.get("weather_code", 0)
                weather_description = self.weather_codes.get(weather_code, "Unknown")
                
                return {
                    "location": location_name,
                    "latitude": latitude,
                    "longitude": longitude,
                    "temperature": current.get("temperature_2m"),
                    "weather_code": weather_code,
                    "weather_description": weather_description,
                    "wind_speed": current.get("wind_speed_10m"),
                    "humidity": current.get("relative_humidity_2m")
                }
                
        except httpx.HTTPError as e:
            raise Exception(f"Weather API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to fetch weather data: {str(e)}")
    
    def format_weather_for_llm(self, weather_data: Dict[str, any]) -> str:
        return (
            f"Location: {weather_data['location']}, "
            f"Temperature: {weather_data['temperature']}°C, "
            f"Condition: {weather_data['weather_description']}, "
            f"Wind Speed: {weather_data['wind_speed']} km/h, "
            f"Humidity: {weather_data['humidity']}%"
        )
