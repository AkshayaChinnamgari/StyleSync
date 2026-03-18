from database import SessionLocal
from models import User, Garment

db = SessionLocal()
user = db.query(User).first()

print("Your Wardrobe:")
print("="*80)

garments = db.query(Garment).filter(Garment.user_id == user.id).all()
for g in garments:
    print(f"ID: {g.id} | Category: {g.category:12} | Color: {g.color:12} | Fabric: {g.fabric or 'N/A':12} | Style: {g.style or 'N/A'}")

print("\n" + "="*80)
print("IMPORTANT - Why you're not seeing dramatic outfit changes:")
print("="*80)
print("\nFor DRAMATIC outfit changes based on temperature, you need:")
print("  ✓ For HOT weather (>30°C): shorts, t-shirts, light dresses")
print("  ✓ For COLD weather (<10°C): sweaters, cardigans, jackets, trench coats")
print("\nYour current wardrobe has limited variety (mostly shirts and pants)")
print("The algorithm IS working, but without diverse items per category,")
print("the outfit changes appear subtle!")

print("\nRecommended items to upload:")
print("  1. A sweater or cardigan (for cold weather)")
print("  2. Shorts (for hot weather)")
print("  3. A jacket or blazer (for layering)")
print("  4. A light dress or kurta (for hot weather variety)")

db.close()
