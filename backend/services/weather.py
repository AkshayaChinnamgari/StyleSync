# backend/services/weather.py
import requests
from typing import Dict, Optional
from config import settings

# City-based weather patterns for fallback (real-world approximations)
CITY_WEATHER_PATTERNS = {
    "hyderabad": {"temp": 28, "condition": "Clear", "humidity": 65, "season": "hot"},
    "delhi": {"temp": 22, "condition": "Haze", "humidity": 55, "season": "moderate"},
    "mumbai": {"temp": 26, "condition": "Humid", "humidity": 75, "season": "humid"},
    "bangalore": {"temp": 24, "condition": "Clear", "humidity": 60, "season": "moderate"},
    "london": {"temp": 12, "condition": "Cloudy", "humidity": 70, "season": "cool"},
    "new york": {"temp": 15, "condition": "Clear", "humidity": 60, "season": "cool"},
    "dubai": {"temp": 35, "condition": "Sunny", "humidity": 40, "season": "hot"},
    "singapore": {"temp": 28, "condition": "Rainy", "humidity": 80, "season": "humid"},
    "tokyo": {"temp": 18, "condition": "Clear", "humidity": 65, "season": "moderate"},
    "paris": {"temp": 14, "condition": "Cloudy", "humidity": 68, "season": "cool"},
    "sydney": {"temp": 22, "condition": "Sunny", "humidity": 55, "season": "moderate"},
    "toronto": {"temp": 10, "condition": "Clear", "humidity": 60, "season": "cold"},
}

def get_weather(city: str) -> Dict:
    """
    Get weather information for a city using OpenWeatherMap API.
    Falls back to city-based patterns if API unavailable.
    
    Returns:
        dict: Contains 'condition', 'temp', 'humidity', 'wind_speed', 'feels_like'
    """
    # Try real API first if key is available
    if settings.openweather_api_key:
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={settings.openweather_api_key}&units=metric"
            response = requests.get(url, timeout=settings.weather_timeout_seconds).json()

            if response.get("cod") == 200 and "weather" in response and "main" in response:
                return {
                    "condition": response["weather"][0]["main"],
                    "description": response["weather"][0]["description"],
                    "temp": response["main"]["temp"],
                    "feels_like": response["main"].get("feels_like", response["main"]["temp"]),
                    "humidity": response["main"].get("humidity", 50),
                    "wind_speed": response["wind"].get("speed", 0) if "wind" in response else 0,
                    "city": city,
                    "source": "api"
                }
        except Exception as e:
            # Log error but continue to fallback
            pass
    
    # Fallback to city-based patterns
    return get_city_based_weather(city)


def get_city_based_weather(city: str) -> Dict:
    """
    Return weather based on city patterns.
    This ensures different recommendations for different cities even without API.
    """
    city_lower = city.lower().strip()
    
    # Try exact match
    if city_lower in CITY_WEATHER_PATTERNS:
        pattern = CITY_WEATHER_PATTERNS[city_lower]
        return {
            "condition": pattern["condition"],
            "description": f"{pattern['season']} weather - {pattern['condition']}",
            "temp": pattern["temp"],
            "feels_like": pattern["temp"],
            "humidity": pattern["humidity"],
            "wind_speed": 3,  # Average wind
            "city": city,
            "source": "patterns"
        }
    
    # Try partial match (e.g., "london" matches "Greater London")
    for pattern_city, pattern in CITY_WEATHER_PATTERNS.items():
        if pattern_city in city_lower or city_lower in pattern_city:
            return {
                "condition": pattern["condition"],
                "description": f"{pattern['season']} weather - {pattern['condition']}",
                "temp": pattern["temp"],
                "feels_like": pattern["temp"],
                "humidity": pattern["humidity"],
                "wind_speed": 3,
                "city": city,
                "source": "patterns"
            }
    
    # Smart guess based on season/region detection
    return infer_weather_by_context(city)


def infer_weather_by_context(city: str) -> Dict:
    """
    Infer weather based on common city keywords if not in database.
    """
    city_lower = city.lower()
    
    # Tropical regions
    if any(x in city_lower for x in ["bangkok", "bali", "caribbean", "miami", "cancun", "phuket"]):
        return {
            "condition": "Humid",
            "description": "tropical weather",
            "temp": 30,
            "feels_like": 32,
            "humidity": 75,
            "wind_speed": 4,
            "city": city,
            "source": "inference"
        }
    
    # Temperate regions
    if any(x in city_lower for x in ["berlin", "amsterdam", "vienna", "prague"]):
        return {
            "condition": "Cloudy",
            "description": "temperate weather",
            "temp": 13,
            "feels_like": 12,
            "humidity": 65,
            "wind_speed": 5,
            "city": city,
            "source": "inference"
        }
    
    # Desert regions
    if any(x in city_lower for x in ["desert", "cairo", "riyadh", "las vegas", "phoenix"]):
        return {
            "condition": "Sunny",
            "description": "dry desert weather",
            "temp": 32,
            "feels_like": 34,
            "humidity": 35,
            "wind_speed": 6,
            "city": city,
            "source": "inference"
        }
    
    # Cold regions
    if any(x in city_lower for x in ["moscow", "alaska", "moscow", "alaska", "reykjavik", "yellowknife"]):
        return {
            "condition": "Clear",
            "description": "cold weather",
            "temp": 5,
            "feels_like": 2,
            "humidity": 50,
            "wind_speed": 8,
            "city": city,
            "source": "inference"
        }
    
    # Mountain regions
    if any(x in city_lower for x in ["aspen", "banff", "zermatt", "chamonix", "whistler"]):
        return {
            "condition": "Clear",
            "description": "cool mountain weather",
            "temp": 8,
            "feels_like": 5,
            "humidity": 55,
            "wind_speed": 7,
            "city": city,
            "source": "inference"
        }
    
    # Default fallback (moderately warm and clear)
    return {
        "condition": "Clear",
        "description": "moderate weather",
        "temp": 22,
        "feels_like": 22,
        "humidity": 60,
        "wind_speed": 4,
        "city": city,
        "source": "default"
    }


def get_clothing_recommendations_for_weather(weather_data: Dict) -> list:
    """
    Get recommended clothing categories based on weather conditions.
    This ensures different recommendations for different weather patterns.
    
    Args:
        weather_data: Dictionary from get_weather()
    
    Returns:
        list: List of recommended clothing categories
    """
    recommendations = []
    temp = weather_data.get("temp", 22)
    condition = weather_data.get("condition", "Clear").lower()
    humidity = weather_data.get("humidity", 60)
    
    # Temperature-based recommendations
    if temp <= 0:
        # Freezing
        recommendations.extend(["trench_coat", "cardigan", "sweater", "jacket"])
        recommendations.append("pants")
    elif temp < 5:
        # Very Cold
        recommendations.extend(["trench_coat", "cardigan", "sweater", "jacket"])
        recommendations.append("pants")
    elif temp < 10:
        # Cold
        recommendations.extend(["cardigan", "sweater", "jacket"])
        recommendations.append("pants")
    elif temp < 15:
        # Cool
        recommendations.extend(["cardigan", "sweater"])
        recommendations.append("pants")
    elif temp < 20:
        # Cool-Moderate
        recommendations.extend(["cardigan", "shirt"])
    elif temp < 25:
        # Moderate
        recommendations.extend(["shirt", "kurta"])
    elif temp < 30:
        # Warm
        recommendations.extend(["shirt", "kurta", "dress"])
    else:
        # Hot
        recommendations.extend(["shirt", "kurta", "dress", "shorts"])
    
    # Weather condition specific recommendations
    if "rain" in condition or "drizzle" in condition:
        recommendations.append("trench_coat")
        if "pants" not in recommendations:
            recommendations.append("pants")
    
    if "clear" in condition or "sunny" in condition:
        if "short" not in str(recommendations):
            recommendations.append("shorts")
        recommendations.append("sunglasses")
    
    if "cloud" in condition:
        recommendations.extend(["cardigan", "jacket"])
    
    if "humid" in condition or humidity > 70:
        # Breathable fabrics for humid weather
        recommendations.extend(["shirt", "kurta", "dress"])
    
    if "haze" in condition or "smoke" in condition:
        recommendations.extend(["scarf", "mask"])
    
    # Always include basics (if not already included)
    if not any(cat in recommendations for cat in ["pants", "shorts", "skirt"]):
        if temp > 25:
            recommendations.append("shorts")
        else:
            recommendations.append("pants")
    
    if not any(cat in recommendations for cat in ["shoes", "boots", "sandals"]):
        if temp > 20:
            recommendations.append("sandals")
        else:
            recommendations.append("shoes")
    
    return list(set(recommendations))  # Remove duplicates
