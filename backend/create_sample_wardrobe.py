from PIL import Image, ImageDraw
from database import SessionLocal
from models import User, Garment
from datetime import datetime
import os

db = SessionLocal()
user = db.query(User).first()

# Create upload directory if it doesn't exist
upload_dir = "static/uploads"
os.makedirs(upload_dir, exist_ok=True)

def create_clothing_image(filename, color_rgb, category_name):
    """Create a simple clothing item image."""
    img = Image.new('RGB', (400, 500), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw garment shape based on category
    if category_name == "shorts":
        # Draw shorts
        draw.rectangle([50, 150, 350, 280], fill=color_rgb, outline='black', width=3)
        draw.line([150, 150, 150, 280], fill='black', width=2)
        draw.ellipse([100, 130, 200, 170], fill=color_rgb, outline='black', width=2)
        draw.ellipse([200, 130, 300, 170], fill=color_rgb, outline='black', width=2)
        draw.text((120, 350), "SHORTS", fill='black', font=None)
        
    elif category_name == "sweater":
        # Draw sweater
        draw.rectangle([80, 100, 320, 350], fill=color_rgb, outline='black', width=3)
        # Sleeves
        draw.ellipse([20, 130, 80, 250], fill=color_rgb, outline='black', width=2)
        draw.ellipse([320, 130, 380, 250], fill=color_rgb, outline='black', width=2)
        # Neckline
        draw.arc([160, 80, 240, 140], 0, 360, fill='black', width=2)
        draw.text((110, 380), "SWEATER", fill='black', font=None)
        
    elif category_name == "jacket":
        # Draw jacket
        draw.rectangle([70, 100, 330, 360], fill=color_rgb, outline='black', width=3)
        # Lapels
        draw.line([200, 100, 150, 200], fill='black', width=2)
        draw.line([200, 100, 250, 200], fill='black', width=2)
        # Sleeves longer than sweater
        draw.rectangle([30, 130, 70, 280], fill=color_rgb, outline='black', width=2)
        draw.rectangle([330, 130, 370, 280], fill=color_rgb, outline='black', width=2)
        draw.text((120, 390), "JACKET", fill='black', font=None)
        
    elif category_name == "dress":
        # Draw dress
        draw.polygon([(150, 80), (250, 80), (350, 400), (50, 400)], fill=color_rgb, outline='black')
        draw.width = 3
        # Straps
        draw.rectangle([160, 70, 180, 90], fill='black')
        draw.rectangle([220, 70, 240, 90], fill='black')
        draw.text((110, 430), "DRESS", fill='black', font=None)
    
    img.save(filename)
    print(f"✓ Created: {filename}")

# Define new clothing items to add
new_items = [
    {
        "filename": "shorts_blue.png",
        "category": "shorts",
        "color": "#1E90FF",
        "style": "casual",
        "fabric": "cotton",
        "description": "Light blue casual shorts",
        "color_rgb": (30, 144, 255)
    },
    {
        "filename": "shorts_khaki.png",
        "category": "shorts",
        "color": "#F0E68C",
        "style": "casual",
        "fabric": "cotton",
        "description": "Khaki casual shorts",
        "color_rgb": (240, 230, 140)
    },
    {
        "filename": "sweater_gray.png",
        "category": "sweater",
        "color": "#808080",
        "style": "casual",
        "fabric": "wool",
        "description": "Gray wool sweater",
        "color_rgb": (128, 128, 128)
    },
    {
        "filename": "sweater_maroon.png",
        "category": "sweater",
        "color": "#800000",
        "style": "casual",
        "fabric": "wool",
        "description": "Maroon wool sweater",
        "color_rgb": (128, 0, 0)
    },
    {
        "filename": "jacket_black.png",
        "category": "jacket",
        "color": "#000000",
        "style": "formal",
        "fabric": "polyester",
        "description": "Black formal jacket",
        "color_rgb": (0, 0, 0)
    },
    {
        "filename": "jacket_navy.png",
        "category": "jacket",
        "color": "#000080",
        "style": "formal",
        "fabric": "wool",
        "description": "Navy wool jacket",
        "color_rgb": (0, 0, 128)
    },
    {
        "filename": "dress_red.png",
        "category": "dress",
        "color": "#FF3333",
        "style": "formal",
        "fabric": "silk",
        "description": "Red silk formal dress",
        "color_rgb": (255, 51, 51)
    },
    {
        "filename": "dress_yellow.png",
        "category": "dress",
        "color": "#FFD700",
        "style": "casual",
        "fabric": "cotton",
        "description": "Yellow cotton summer dress",
        "color_rgb": (255, 215, 0)
    },
]

print("Creating sample clothing images...")
print("=" * 80)

# Create images and add to database
for item in new_items:
    filepath = f"{upload_dir}/{item['filename']}"
    color_rgb = item.pop("color_rgb")
    category = item.pop("category")
    
    # Create the image
    create_clothing_image(filepath, color_rgb, category)
    
    # Add to database
    garment = Garment(
        user_id=user.id,
        filename=item['filename'],
        color=item['color'],
        category=category,
        style=item['style'],
        fabric=item['fabric'],
        season='all',
        size='M',
        description=item['description'],
        uploaded_at=datetime.utcnow()
    )
    db.add(garment)

db.commit()

print("\n" + "=" * 80)
print("✅ Successfully added 8 new clothing items to your wardrobe!")
print("=" * 80)

# Show updated wardrobe
print("\nYour Updated Wardrobe:")
print("-" * 80)
garments = db.query(Garment).filter(Garment.user_id == user.id).all()
print(f"Total items: {len(garments)}\n")

by_category = {}
for g in garments:
    cat = g.category
    if cat not in by_category:
        by_category[cat] = []
    by_category[cat].append(g)

for category in sorted(by_category.keys()):
    count = len(by_category[category])
    items = by_category[category]
    print(f"  {category.upper():12} ({count} items)")
    for g in items:
        print(f"    • {g.color:12} - {g.fabric or 'N/A':12} - {g.description}")

print("\n" + "=" * 80)
print("Now test with different cities:")
print("  • Dubai (35°C) → Should recommend SHORTS + shirt")
print("  • London (12°C) → Should recommend SWEATER + JACKET + pants")
print("  • Hyderabad (28°C) → Should recommend SHORTS/light items + shirt")
print("=" * 80)

db.close()
