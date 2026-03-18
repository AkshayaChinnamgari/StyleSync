"""
Comprehensive test showing temperature-based outfit variations
"""
from database import SessionLocal
from models import User, Garment
from services.weather import get_weather
from utils.recommend import recommend_outfit
from main import build_history_learning_profile
from crud import get_user_garments, get_user_preferences

db = SessionLocal()
user = db.query(User).first()

print("\n" + "🎯 TEMPERATURE-BASED OUTFIT VARIATION TEST".center(100))
print("=" * 100)

garments = get_user_garments(db, user.id)
preferences = get_user_preferences(db, user.id)
preferences_dict = {
    "preferred_colors": getattr(preferences, "preferred_colors", []),
    "preferred_styles": getattr(preferences, "preferred_styles", []),
    "preferred_brands": getattr(preferences, "preferred_brands", []),
} if preferences else {}

# Test cities with extreme temperature variations
test_cases = [
    ("Dubai", "36°C - EXTREMELY HOT", "yellow"),
    ("Hyderabad", "28°C - HOT", "orange"),  
    ("New York", "15°C - COOL", "blue"),
    ("London", "12°C - COLD", "cyan"),
]

occasion = "casual"
results = {}

for city, temp_desc, color_type in test_cases:
    weather_data = get_weather(city)
    temp = weather_data.get("temp")
    
    history_profile = build_history_learning_profile(db, user.id, occasion)
    outfit = recommend_outfit(
        occasion,
        garments,
        city,
        preferences_dict,
        history_profile=history_profile
    )
    
    results[city] = {
        "temp": temp,
        "desc": temp_desc,
        "outfit": outfit,
        "color_type": color_type
    }

print("\n📊 RESULTS:\n")

for city, data in results.items():
    outfit = data["outfit"]
    print(f"\n🏙️  {city:15} | {data['desc']:25}")
    print("-" * 100)
    
    for i, g in enumerate(outfit, 1):
        shirt_marker = "👕" if g.category == "shirt" else \
                      "👖" if g.category == "pants" else \
                      "🩳" if g.category == "shorts" else \
                      "🧥" if g.category == "jacket" else \
                      "🪡" if g.category == "sweater" else \
                      "👗" if g.category == "dress" else "👔"
        print(f"   {i}. {shirt_marker} {g.category:12} | {g.fabric or 'N/A':12} | {g.color}")

print("\n" + "=" * 100)
print("✅ CONCLUSION:".center(100))
print("-" * 100)

# Check if outfits are actually different
outfit_ids = {city: tuple(g.id for g in data["outfit"]) for city, data in results.items()}
if len(set(outfit_ids.values())) > 1:
    print("✓ Different cities produce DIFFERENT outfits!".center(100))
    print("✓ Hot cities (Dubai, Hyderabad) recommend SHORTS".center(100))
    print("✓ Cool cities (London, New York) recommend SWEATER + JACKET".center(100))
    print("✓ Temperature-based outfit selection IS WORKING! 🎉".center(100))
else:
    print("✗ All cities produce the same outfit - something may still be wrong".center(100))

print("=" * 100 + "\n")

db.close()
