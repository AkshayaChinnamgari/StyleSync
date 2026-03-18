"""
CRUD operations for StyleSync application.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import User, Garment, OutfitHistory, OutfitItem, UserPreferences
from auth import hash_password
from typing import List, Optional

# Standard color palette used throughout the application
STANDARD_PALETTE = [
    '#000000', '#FFFFFF', '#808080', '#FF0000', '#00FF00', '#0000FF',
    '#FFFF00', '#FFC0CB', '#A52A2A', '#FFA500', '#800080', '#008080'
]


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple with robust error handling."""
    try:
        hex_color = str(hex_color).strip()
        if not hex_color.startswith('#'):
            hex_color = '#' + hex_color
        hex_color = hex_color.upper()
        
        if len(hex_color) == 4:
            hex_color = '#' + ''.join([c*2 for c in hex_color[1:]])
        
        if len(hex_color) != 7:
            return (128, 128, 128)
        
        hex_digits = hex_color[1:]
        return tuple(int(hex_digits[i:i+2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError, TypeError):
        return (128, 128, 128)


def rgb_to_hsl(r: int, g: int, b: int) -> tuple:
    """Convert RGB to HSL (Hue, Saturation, Lightness)."""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2.0
    
    if max_c == min_c:
        h = s = 0
    else:
        d = max_c - min_c
        s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
        
        if max_c == r:
            h = ((g - b) / d + (6 if g < b else 0)) / 6
        elif max_c == g:
            h = ((b - r) / d + 2) / 6
        else:
            h = ((r - g) / d + 4) / 6
    
    return (int(h * 360), int(s * 100), int(l * 100))


def classify_color_by_hue(hex_color: str) -> str:
    """Classify color by hue (more accurate than RGB distance for human perception)."""
    try:
        r, g, b = hex_to_rgb(hex_color)
        h, s, l = rgb_to_hsl(r, g, b)
        
        # Handle grayscale
        if s < 10:
            return '#000000' if l < 30 else '#FFFFFF' if l > 85 else '#808080'
        
        # Classify by hue
        if h < 15 or h >= 345:
            return '#FF0000'  # Red
        elif h < 45:
            return '#FFA500'  # Orange
        elif h < 65:
            return '#FFFF00'  # Yellow
        elif h < 150:
            return '#00FF00'  # Green
        elif h < 200:
            return '#00FFFF'  # Cyan
        elif h < 260:
            return '#0000FF'  # Blue
        elif h < 290:
            return '#800080'  # Purple
        elif h < 330:
            return '#FFC0CB'  # Pink
        else:
            return '#FF0000'  # Default Red
    except Exception:
        return '#808080'  # Gray on error


def color_distance(hex1: str, hex2: str) -> float:
    """Calculate Euclidean distance between two hex colors in RGB space."""
    try:
        r1, g1, b1 = hex_to_rgb(hex1)
        r2, g2, b2 = hex_to_rgb(hex2)
        return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5
    except (ValueError, IndexError, TypeError):
        return 999.0

# ==================== User Operations ====================

def create_user(db: Session, username: str, email: str, password: str) -> User:
    """Create a new user with hashed password."""
    hashed_pwd = hash_password(password)
    user = User(username=username, email=email, hashed_password=hashed_pwd)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create default preferences
    preferences = UserPreferences(user_id=user.id)
    db.add(preferences)
    db.commit()
    
    return user


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


# ==================== Garment Operations ====================

def save_garment(db: Session, user_id: int, filename: str, color: str, category: str,
                 style: str = None, season: str = None, fabric: str = None, size: str = None,
                 brand: str = None, description: str = None) -> Garment:
    """Save a garment to the database."""
    garment = Garment(
        user_id=user_id,
        filename=filename,
        color=color,
        category=category,
        style=style or "casual",
        season=season or "all",
        fabric=fabric,
        size=size,
        brand=brand,
        description=description
    )
    db.add(garment)
    db.commit()
    db.refresh(garment)
    return garment


def get_user_garments(db: Session, user_id: int) -> List[Garment]:
    """Get all garments for a user."""
    return db.query(Garment).filter(Garment.user_id == user_id).all()


def get_garment(db: Session, garment_id: int, user_id: int) -> Optional[Garment]:
    """Get a specific garment (with user verification)."""
    return db.query(Garment).filter(
        Garment.id == garment_id,
        Garment.user_id == user_id
    ).first()


def delete_garment(db: Session, garment_id: int, user_id: int) -> bool:
    """Delete a garment."""
    garment = get_garment(db, garment_id, user_id)
    if garment:
        db.delete(garment)
        db.commit()
        return True
    return False


def update_garment(db: Session, garment_id: int, user_id: int, **kwargs) -> Optional[Garment]:
    """Update garment attributes."""
    garment = get_garment(db, garment_id, user_id)
    if garment:
        for key, value in kwargs.items():
            if hasattr(garment, key) and value is not None:
                setattr(garment, key, value)
        db.commit()
        db.refresh(garment)
    return garment


def filter_garments(db: Session, user_id: int, category: str = None,
                   color: str = None, style: str = None, season: str = None,
                   fabric: str = None) -> List[Garment]:
    """Filter garments by various attributes with smart hue-based color matching."""
    query = db.query(Garment).filter(Garment.user_id == user_id)
    
    if category:
        query = query.filter(Garment.category == category)
    if style:
        query = query.filter(Garment.style == style)
    if season:
        query = query.filter(Garment.season == season)
    if fabric:
        query = query.filter(Garment.fabric == fabric)
    
    # Get initial results before color filtering
    results = query.all()
    
    # Apply color filtering using hue-based classification
    if color:
        color_upper = color.upper()
        filtered_results = []
        for garment in results:
            if garment.color:
                classified_color = classify_color_by_hue(garment.color)
                # Only include if classified color matches the selected color
                if classified_color.upper() == color_upper:
                    filtered_results.append(garment)
        results = filtered_results
    
    return results


def search_garments(db: Session, user_id: int, query_text: str) -> List[Garment]:
    """Search garments by filename or description. Returns unique results."""
    query_text = query_text.strip()
    results = db.query(Garment).filter(
        Garment.user_id == user_id,
        (Garment.filename.ilike(f"%{query_text}%")) |
        (Garment.description.ilike(f"%{query_text}%")) |
        (Garment.brand.ilike(f"%{query_text}%")) |
        (Garment.color.ilike(f"%{query_text}%")) |
        (Garment.style.ilike(f"%{query_text}%")) |
        (Garment.category.ilike(f"%{query_text}%")) |
        (Garment.fabric.ilike(f"%{query_text}%"))
    ).distinct(Garment.id).all()
    
    # Remove duplicates in case any exist
    seen = set()
    unique_results = []
    for garment in results:
        if garment.id not in seen:
            seen.add(garment.id)
            unique_results.append(garment)
    
    return unique_results


# ==================== Outfit History Operations ====================

def create_outfit_record(db: Session, user_id: int, garment_ids: List[int], 
                         occasion: str, rating: int = None, notes: str = None) -> OutfitHistory:
    """Create an outfit history record."""
    outfit = OutfitHistory(
        user_id=user_id,
        occasion=occasion,
        rating=rating,
        notes=notes
    )
    db.add(outfit)
    db.flush()  # Get the ID
    
    # Add garment items
    for garment_id in garment_ids:
        outfit_item = OutfitItem(outfit_id=outfit.id, garment_id=garment_id)
        db.add(outfit_item)
    
    db.commit()
    db.refresh(outfit)
    return outfit


def get_user_outfit_history(db: Session, user_id: int) -> List[OutfitHistory]:
    """Get all outfit history for a user."""
    return db.query(OutfitHistory).filter(OutfitHistory.user_id == user_id).all()


def get_outfit(db: Session, outfit_id: int, user_id: int) -> Optional[OutfitHistory]:
    """Get a specific outfit (with user verification)."""
    return db.query(OutfitHistory).filter(
        OutfitHistory.id == outfit_id,
        OutfitHistory.user_id == user_id
    ).first()


def rate_outfit(db: Session, outfit_id: int, user_id: int, rating: int) -> Optional[OutfitHistory]:
    """Rate an outfit."""
    outfit = get_outfit(db, outfit_id, user_id)
    if outfit and 1 <= rating <= 5:
        outfit.rating = rating
        db.commit()
        db.refresh(outfit)
    return outfit


# ==================== User Preferences Operations ====================

def update_user_preferences(db: Session, user_id: int, **kwargs) -> Optional[UserPreferences]:
    """Update user style preferences."""
    preferences = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    if preferences:
        for key, value in kwargs.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)
        db.commit()
        db.refresh(preferences)
    return preferences


def get_user_preferences(db: Session, user_id: int) -> Optional[UserPreferences]:
    """Get user preferences."""
    return db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()


def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
    """Update user fields (body_type, style_type, gender, age, etc)."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user
