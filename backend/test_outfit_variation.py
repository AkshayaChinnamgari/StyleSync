from database import SessionLocal
from models import User
from utils.recommend import recommend_outfit
from crud import get_user_garments, get_user_preferences
from main import build_history_learning_profile

db = SessionLocal()

# Get first user
user = db.query(User).first()
if not user:
    print("No user found!")
    exit()

print(f"Testing with user: {user.username}")

# Get garments
garments = get_user_garments(db, user.id)
print(f"Total garments: {len(garments)}")

if len(garments) < 3:
    print("Not enough garments for testing!")
    exit()

# Get preferences
preferences = get_user_preferences(db, user.id)
preferences_dict = {
    "preferred_colors": getattr(preferences, "preferred_colors", []),
    "preferred_styles": getattr(preferences, "preferred_styles", []),
    "preferred_brands": getattr(preferences, "preferred_brands", []),
} if preferences else {}

# Test with different cities
test_cities = ["Hyderabad", "London", "Dubai"]
occasion = "casual"

results = {}

for city in test_cities:
    print(f"\n{'='*50}")
    print(f"City: {city}")
    print('='*50)
    
    history_profile = build_history_learning_profile(db, user.id, occasion)
    
    outfit = recommend_outfit(
        occasion,
        garments,
        city,
        preferences_dict,
        history_profile=history_profile
    )
    
    print(f"Garments recommended: {len(outfit)}")
    outfit_ids = []
    for i, garment in enumerate(outfit):
        print(f"  {i+1}. {garment.category} - {garment.color} - ID: {garment.id}")
        outfit_ids.append(garment.id)
    
    results[city] = outfit_ids

# Compare results
print(f"\n{'='*50}")
print("COMPARISON")
print('='*50)

if results["Hyderabad"] == results["London"] == results["Dubai"]:
    print("❌ PROBLEM: All cities returned the same outfit!")
    print(f"   Outfit IDs: {results['Hyderabad']}")
else:
    print("✅ SUCCESS: Different cities returned different outfits!")
    for city, ids in results.items():
        print(f"   {city}: {ids}")

db.close()
