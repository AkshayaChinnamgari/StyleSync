from database import SessionLocal
from models import User, Garment
from services.weather import get_weather
from utils.recommend import recommend_outfit
from main import build_history_learning_profile
from crud import get_user_garments, get_user_preferences

db = SessionLocal()

user = db.query(User).first()
garments = get_user_garments(db, user.id)
preferences = get_user_preferences(db, user.id)
preferences_dict = {
    "preferred_colors": getattr(preferences, "preferred_colors", []),
    "preferred_styles": getattr(preferences, "preferred_styles", []),
    "preferred_brands": getattr(preferences, "preferred_brands", []),
} if preferences else {}

# Test with different cities and show detailed weather info
test_cities = ["Hyderabad", "London", "Dubai", "New York"]
occasion = "casual"

print("DETAILED CITY-BY-CITY ANALYSIS")
print("=" * 100)

for city in test_cities:
    print(f"\n{city.upper()}")
    print("-" * 100)
    
    # Get weather
    weather_data = get_weather(city)
    print(f"Weather: {weather_data.get('temp')}°C, {weather_data.get('condition')}, Humidity: {weather_data.get('humidity')}%")
    
    # Get recommendation
    history_profile = build_history_learning_profile(db, user.id, occasion)
    outfit = recommend_outfit(
        occasion,
        garments,
        city,
        preferences_dict,
        history_profile=history_profile
    )
    
    print(f"Outfit ({len(outfit)} items):")
    for garment in outfit:
        print(f"  • {garment.category:12} - {garment.color:12} - {garment.fabric or 'N/A':10} - ID: {garment.id}")

print("\n" + "=" * 100)
print("EXPECTED BEHAVIOR:")
print("  • Dubai (35°C) → Shorts + light items")
print("  • London (12°C) → Should prioritize SWEATER/JACKET + warm clothing")
print("  • Hyderabad (28°C) → Shorts for comfort")
print("  • New York (15°C) → Maybe cardigan/sweater/jacket")
print("=" * 100)

db.close()
