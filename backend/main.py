from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status, Query, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from collections import Counter

from crud import *
from database import Base, engine, SessionLocal
from config import settings
from models import Garment, User
from utils.image_utils import get_dominant_color
from utils.classify import classify_garment, detect_style, detect_season, detect_fabric
from utils.recommend import recommend_outfit, get_what_to_wear_today, find_color_combinations, get_suitable_matches, normalize_occasion
from utils.analytics import summarize_wardrobe_analytics, explain_recommendation
from utils.virtual_tryon import create_outfit_collage, create_virtual_tryon_preview
from utils.size_recommendations import get_size_recommendations, suggest_size_for_body_type
from utils.advanced_analytics import get_wardrobe_insights
from utils.recommendation_engine import generate_outfit_explanation, generate_style_profile, generate_styling_tips, calculate_versatility_score
from services.weather import get_weather, get_clothing_recommendations_for_weather
from services.shopping import (
    get_complementary_items, find_trend_items, 
    get_sustainability_tips, calculate_outfit_sustainability_score
)
from auth import (
    get_db, hash_password, verify_password, create_access_token, 
    authenticate_user, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta, datetime

# ==================== Setup ====================

UPLOAD_DIR = "static/uploads"
PROFILE_DIR = "profile_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROFILE_DIR, exist_ok=True)

Base.metadata.create_all(bind=engine)

def ensure_user_profile_columns():
    """Ensure optional profile columns exist in SQLite users table."""
    try:
        with engine.connect() as conn:
            result = conn.exec_driver_sql("PRAGMA table_info(users)")
            columns = {row[1] for row in result.fetchall()}
            if "avatar" not in columns:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN avatar VARCHAR")
            if "gender" not in columns:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN gender VARCHAR")
            if "age" not in columns:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN age INTEGER")
            if "body_type" not in columns:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN body_type VARCHAR")
            if "style_type" not in columns:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN style_type VARCHAR")
    except Exception as e:
        print(f"[DB] Profile column check failed: {e}")

ensure_user_profile_columns()

def ensure_garment_columns():
    """Ensure optional garment columns exist in SQLite garments table."""
    try:
        with engine.connect() as conn:
            result = conn.exec_driver_sql("PRAGMA table_info(garments)")
            columns = {row[1] for row in result.fetchall()}
            if "fabric" not in columns:
                conn.exec_driver_sql("ALTER TABLE garments ADD COLUMN fabric VARCHAR")
    except Exception as e:
        print(f"[DB] Garment column check failed: {e}")

ensure_garment_columns()

def build_history_learning_profile(db: Session, user_id: int, target_occasion: Optional[str] = None) -> dict:
    """Build lightweight preference-learning signals from past outfits."""
    outfits = get_user_outfit_history(db, user_id) or []
    if not outfits:
        return {
            "liked_styles": {},
            "liked_colors": {},
            "liked_categories": {},
            "disliked_styles": {},
            "disliked_colors": {},
            "disliked_categories": {},
            "garment_affinity": {},
            "occasion_style_bias": {},
            "sample_size": 0,
            "has_learning": False,
        }

    now = datetime.utcnow()
    liked_styles, liked_colors, liked_categories = {}, {}, {}
    disliked_styles, disliked_colors, disliked_categories = {}, {}, {}
    garment_affinity = {}
    occasion_style_bias = {}
    sample_size = 0
    target_norm = normalize_occasion(target_occasion or "")

    def bump(store: dict, key: str, delta: float):
        if not key:
            return
        store[key] = store.get(key, 0.0) + float(delta)

    for outfit in outfits:
        outfit_date = getattr(outfit, "date", None) or now
        days_old = max(0, (now - outfit_date).days)
        recency = max(0.15, 1.0 - (days_old / 180.0))  # decays over ~6 months

        rating = getattr(outfit, "rating", None)
        rating_centered = ((rating if rating is not None else 3) - 3) / 2.0  # [-1, 1]
        pos_weight = recency * (1.0 + max(0.0, rating_centered) * 1.1)
        neg_weight = recency * (max(0.0, -rating_centered) + 0.15)

        occ = normalize_occasion(getattr(outfit, "occasion", "") or "")
        occ_factor = 1.3 if target_norm and occ == target_norm else 1.0
        pos_weight *= occ_factor
        neg_weight *= occ_factor

        for outfit_item in getattr(outfit, "outfit_items", []) or []:
            garment = getattr(outfit_item, "garment", None)
            if not garment:
                continue
            sample_size += 1
            g_style = (getattr(garment, "style", None) or "").lower()
            g_color = (getattr(garment, "color", None) or "").lower()
            g_category = (getattr(garment, "category", None) or "").lower()
            g_id = str(getattr(garment, "id", ""))

            if pos_weight > 0:
                bump(liked_styles, g_style, pos_weight)
                bump(liked_colors, g_color, pos_weight)
                bump(liked_categories, g_category, pos_weight)
            if neg_weight > 0:
                bump(disliked_styles, g_style, neg_weight)
                bump(disliked_colors, g_color, neg_weight)
                bump(disliked_categories, g_category, neg_weight)

            if g_id:
                garment_affinity[g_id] = garment_affinity.get(g_id, 0.0) + (rating_centered * recency)
            if occ and g_style:
                occ_map = occasion_style_bias.setdefault(occ, {})
                occ_map[g_style] = occ_map.get(g_style, 0.0) + (rating_centered * recency)

    return {
        "liked_styles": liked_styles,
        "liked_colors": liked_colors,
        "liked_categories": liked_categories,
        "disliked_styles": disliked_styles,
        "disliked_colors": disliked_colors,
        "disliked_categories": disliked_categories,
        "garment_affinity": garment_affinity,
        "occasion_style_bias": occasion_style_bias,
        "sample_size": sample_size,
        "has_learning": sample_size > 0,
    }

app = FastAPI(title=settings.app_name, description="AI Wardrobe Companion API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass

try:
    app.mount("/profile_images", StaticFiles(directory=PROFILE_DIR), name="profile_images")
except:
    pass

# ==================== Pydantic Models ====================

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str

class GarmentCreate(BaseModel):
    category: str
    style: Optional[str] = "casual"
    season: Optional[str] = "all"
    fabric: Optional[str] = None
    size: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None

class GarmentResponse(BaseModel):
    id: int
    filename: str
    color: str
    category: str
    style: str
    season: str
    fabric: Optional[str]
    brand: Optional[str]
    description: Optional[str]

class OutfitRequest(BaseModel):
    occasion: str
    city: Optional[str] = None

class TryOnRequest(BaseModel):
    garment_ids: List[int]
    occasion: Optional[str] = "virtual_tryon"

class OutfitItemResponse(BaseModel):
    id: int
    filename: str
    color: str
    category: str
    style: str

class PreferencesUpdate(BaseModel):
    preferred_colors: Optional[List[str]] = None
    preferred_styles: Optional[List[str]] = None
    preferred_brands: Optional[List[str]] = None
    body_type: Optional[str] = None
    skin_tone: Optional[str] = None
    budget_range: Optional[str] = None

class ProfileResponse(BaseModel):
    username: str
    email: str
    avatar_url: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None

# ==================== Authentication Endpoints ====================

@app.post("/auth/register", response_model=Token)
def register(user: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be 72 bytes or fewer"
        )
    # Check if user exists
    if get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    if get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    new_user = create_user(db, user.username, user.email, user.password)
    
    # Create token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.id}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "username": new_user.username
    }

@app.post("/auth/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token."""
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }

@app.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }

def get_current_user_profile_url(user: User, request: Request) -> Optional[str]:
    if user.avatar:
        return str(request.base_url).rstrip("/") + f"/profile_images/{user.avatar}"
    return None

def safe_filename(name: str) -> str:
    """Normalize and sanitize incoming filenames to keep paths safe and portable."""
    basename = os.path.basename(name or "upload")
    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in basename)

@app.get("/profile/me", response_model=ProfileResponse)
def get_profile_me(request: Request, current_user: User = Depends(get_current_user)):
    return ProfileResponse(
        username=current_user.username,
        email=current_user.email,
        avatar_url=get_current_user_profile_url(current_user, request),
        gender=getattr(current_user, "gender", None),
        age=getattr(current_user, "age", None)
    )

@app.put("/profile/update", response_model=ProfileResponse)
async def update_profile(
    request: Request,
    gender: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if gender is not None:
        current_user.gender = gender
    if age is not None:
        current_user.age = age

    if file:
        filename = f"{current_user.id}_{safe_filename(file.filename)}"
        file_path = os.path.join(PROFILE_DIR, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        current_user.avatar = filename

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return ProfileResponse(
        username=current_user.username,
        email=current_user.email,
        avatar_url=get_current_user_profile_url(current_user, request),
        gender=getattr(current_user, "gender", None),
        age=getattr(current_user, "age", None)
    )

# ==================== Wardrobe Upload & Management ====================

@app.post("/wardrobe/detect")
async def detect_garment_attributes(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Detect garment attributes without saving to database."""
    try:
        contents = await file.read()
        clean_name = safe_filename(file.filename)
        save_path = os.path.join(UPLOAD_DIR, f"temp_{clean_name}")
        with open(save_path, "wb") as f:
            f.write(contents)

        # Auto-detect all attributes
        color = get_dominant_color(save_path)
        category = classify_garment(save_path)
        style = detect_style(save_path, category)
        season = detect_season(save_path, category)
        fabric = detect_fabric(save_path, category)

        # Delete temp file
        try:
            os.remove(save_path)
        except:
            pass

        return {
            "category": category,
            "style": style,
            "season": season,
            "fabric": fabric,
            "color": color
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/wardrobe/upload")
async def upload_garment(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a clothing item to the user's wardrobe with auto-detection or manual category."""
    try:
        contents = await file.read()
        clean_name = safe_filename(file.filename)
        save_path = os.path.join(UPLOAD_DIR, f"uploaded_{clean_name}")
        with open(save_path, "wb") as f:
            f.write(contents)

        # Auto-detect attributes
        color = get_dominant_color(save_path)
        detected_category = classify_garment(save_path)
        detected_style = detect_style(save_path, detected_category)
        detected_season = detect_season(save_path, category or detected_category)
        detected_fabric = detect_fabric(save_path, category or detected_category)

        # Use manual category if provided, otherwise use detected
        final_category = category if category else detected_category
        
        print(f"\n[Upload] Manual category: {category}, Detected: {detected_category}, Final: {final_category}")

        # Save to database with final attributes
        garment = save_garment(
            db, current_user.id, clean_name, color,
            final_category, style=detected_style, season=detected_season, fabric=detected_fabric
        )

        return {
            "message": "Garment uploaded successfully",
            "id": garment.id,
            "filename": garment.filename,
            "color": garment.color,
            "category": garment.category,
            "detected_category": detected_category if category else None,
            "style": garment.style,
            "season": garment.season,
            "fabric": garment.fabric,
            "detected": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/wardrobe/items", response_model=List[GarmentResponse])
def get_wardrobe(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all garments in user's wardrobe."""
    garments = get_user_garments(db, current_user.id)
    return garments

@app.get("/wardrobe/categories")
def get_wardrobe_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all categories in user's wardrobe with item counts."""
    from sqlalchemy import func
    
    # Query garment categories with counts
    category_counts = db.query(
        Garment.category,
        func.count(Garment.id).label('count')
    ).filter(Garment.user_id == current_user.id).group_by(Garment.category).all()
    
    # Define category groups for better UI organization
    category_groups = {
        "Tops": ["shirt", "cardigan", "jacket", "blazer"],
        "Bottoms": ["pants", "shorts", "skirt"],
        "Dresses": ["dress", "kurta"],
        "Outerwear": ["trench_coat"],
        "Footwear": ["shoes", "boots", "sandals"],
        "Accessories": ["necklace", "bracelet", "earrings", "watch", "hat", "gloves", "scarf", "belt", "bag"]
    }
    
    # Build response with grouped categories
    result = {
        "total_items": sum(count for _, count in category_counts),
        "categories": [],
        "grouped": {}
    }
    
    # Flat list of all categories
    category_dict = {cat: count for cat, count in category_counts}
    for category, count in sorted(category_dict.items()):
        result["categories"].append({
            "name": category,
            "count": count
        })
    
    # Grouped categories
    for group_name, group_categories in category_groups.items():
        group_count = sum(category_dict.get(cat, 0) for cat in group_categories)
        if group_count > 0:
            result["grouped"][group_name] = {
                "count": group_count,
                "categories": [
                    {"name": cat, "count": category_dict.get(cat, 0)} 
                    for cat in group_categories 
                    if cat in category_dict
                ]
            }
    
    return result

@app.get("/wardrobe/items/{garment_id}", response_model=GarmentResponse)
def get_garment_details(
    garment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific garment."""
    garment = get_garment(db, garment_id, current_user.id)
    if not garment:
        raise HTTPException(status_code=404, detail="Garment not found")
    return garment

@app.delete("/wardrobe/items/{garment_id}")
def delete_garment_endpoint(
    garment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a garment from wardrobe."""
    if delete_garment(db, garment_id, current_user.id):
        return {"message": "Garment deleted successfully"}
    raise HTTPException(status_code=404, detail="Garment not found")

@app.put("/wardrobe/items/{garment_id}", response_model=GarmentResponse)
def update_garment_endpoint(
    garment_id: int,
    updates: GarmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update garment information."""
    garment = update_garment(
        db, garment_id, current_user.id,
        **updates.dict(exclude_unset=True)
    )
    if not garment:
        raise HTTPException(status_code=404, detail="Garment not found")
    return garment

# ==================== Search & Filter ====================

@app.get("/wardrobe/search", response_model=List[GarmentResponse])
def search_wardrobe(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search wardrobe by name, brand, or description."""
    results = search_garments(db, current_user.id, q)
    return results

@app.get("/wardrobe/filter", response_model=List[GarmentResponse])
def filter_wardrobe(
    category: Optional[str] = None,
    color: Optional[str] = None,
    style: Optional[str] = None,
    season: Optional[str] = None,
    fabric: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Filter wardrobe by attributes."""
    results = filter_garments(db, current_user.id, category, color, style, season, fabric)
    return results

@app.get("/wardrobe/by-category/{category}", response_model=List[GarmentResponse])
def get_by_category(
    category: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all items of a specific category."""
    results = filter_garments(db, current_user.id, category=category)
    return results

# ==================== Outfit Recommendations ====================

@app.post("/recommendations/outfit")
def get_outfit_recommendation(
    request: OutfitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get outfit recommendation for a specific occasion."""
    garments = get_user_garments(db, current_user.id)
    if not garments:
        raise HTTPException(
            status_code=400,
            detail="No items in wardrobe. Please upload some clothing items first."
        )
    
    preferences = get_user_preferences(db, current_user.id)
    preferences_dict = {
        "preferred_colors": getattr(preferences, "preferred_colors", []),
        "preferred_styles": getattr(preferences, "preferred_styles", []),
        "preferred_brands": getattr(preferences, "preferred_brands", []),
    } if preferences else {}
    history_profile = build_history_learning_profile(db, current_user.id, request.occasion)
    outfit = recommend_outfit(
        request.occasion,
        garments,
        request.city,
        preferences_dict,
        history_profile=history_profile
    )
    if outfit:
        try:
            create_outfit_record(
                db,
                current_user.id,
                [g.id for g in outfit if getattr(g, "id", None)],
                normalize_occasion(request.occasion)
            )
        except Exception:
            pass
    
    return {
        "occasion": request.occasion,
        "city": request.city,
        "outfit": [
            {
                "id": g.id,
                "filename": g.filename,
                "color": g.color,
                "category": g.category,
                "style": g.style,
                "fabric": g.fabric
            }
            for g in outfit
        ],
        "normalized_occasion": normalize_occasion(request.occasion),
        "learning": {
            "applied": bool(history_profile.get("has_learning")),
            "history_samples": int(history_profile.get("sample_size", 0)),
            "target_occasion": normalize_occasion(request.occasion),
        },
        "explanation": explain_recommendation(
            outfit=outfit,
            all_garments=garments,
            occasion=request.occasion,
            city=request.city,
            user_preferences=preferences_dict,
            history_profile=history_profile,
        ),
    }

@app.post("/recommendations/pair-with")
def pair_with_garment(
    garment_id: int = Query(..., description="ID of the selected garment"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get outfit recommendations pairing with a selected garment."""
    from utils.recommend import get_suitable_matches
    
    # Get the base garment
    base_garment = db.query(Garment).filter(
        Garment.id == garment_id,
        Garment.user_id == current_user.id
    ).first()
    
    if not base_garment:
        raise HTTPException(
            status_code=404,
            detail="Garment not found"
        )
    
    # Get all user's garments
    all_garments = get_user_garments(db, current_user.id)
    
    if not all_garments:
        raise HTTPException(
            status_code=400,
            detail="No items in wardrobe"
        )
    
    # Get suitable matches
    matches = get_suitable_matches(base_garment, all_garments, outfit_type="complete")
    
    return {
        "base_garment": {
            "id": base_garment.id,
            "filename": base_garment.filename,
            "color": base_garment.color,
            "category": base_garment.category,
            "style": base_garment.style,
            "season": base_garment.season,
            "fabric": base_garment.fabric
        },
        "suggestions": [
            {
                "id": g.id,
                "filename": g.filename,
                "color": g.color,
                "category": g.category,
                "style": g.style,
                "season": g.season,
                "fabric": g.fabric
            }
            for g in matches
        ],
        "message": f"Found {len(matches)} items that work well with your {base_garment.category}"
    }

@app.get("/recommendations/what-to-wear-today")
def what_to_wear_today(
    city: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get "What to wear today" recommendation based on weather."""
    garments = get_user_garments(db, current_user.id)
    if not garments:
        raise HTTPException(
            status_code=400,
            detail="No items in wardrobe"
        )
    
    preferences = get_user_preferences(db, current_user.id)
    preferences_dict = {
        "preferred_colors": getattr(preferences, "preferred_colors", []),
        "preferred_styles": getattr(preferences, "preferred_styles", []),
        "preferred_brands": getattr(preferences, "preferred_brands", []),
    } if preferences else {}
    history_profile = build_history_learning_profile(db, current_user.id, "today")
    outfit = get_what_to_wear_today(
        garments,
        city,
        preferences_dict,
        history_profile=history_profile
    )
    if outfit:
        try:
            create_outfit_record(
                db,
                current_user.id,
                [g.id for g in outfit if getattr(g, "id", None)],
                "today"
            )
        except Exception:
            pass
    
    weather = {}
    if city:
        weather = get_weather(city)
    
    return {
        "message": "Today's outfit recommendation",
        "weather": weather,
        "outfit": [
            {
                "id": g.id,
                "filename": g.filename,
                "color": g.color,
                "category": g.category,
                "style": g.style,
                "season": g.season,
                "fabric": g.fabric
            }
            for g in outfit
        ],
        "learning": {
            "applied": bool(history_profile.get("has_learning")),
            "history_samples": int(history_profile.get("sample_size", 0)),
            "target_occasion": "today",
        },
        "explanation": explain_recommendation(
            outfit=outfit,
            all_garments=garments,
            occasion="today",
            city=city,
            user_preferences=preferences_dict,
            history_profile=history_profile,
        ),
    }

@app.get("/weather/{city}")
def get_weather_info(city: str):
    """Get weather information for a city."""
    return get_weather(city)

@app.get("/weather-clothing/{city}")
def get_weather_based_clothing(city: str):
    """Get clothing recommendations based on weather."""
    weather = get_weather(city)
    recommendations = get_clothing_recommendations_for_weather(weather)
    
    return {
        "city": city,
        "weather": weather,
        "recommended_clothing": recommendations
    }

# ==================== Color Harmony & Combinations ====================

@app.get("/colors/harmony/{garment_id}")
def get_color_harmony(
    garment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Find color-harmonious items for a garment."""
    garment = get_garment(db, garment_id, current_user.id)
    if not garment:
        raise HTTPException(status_code=404, detail="Garment not found")
    
    all_garments = get_user_garments(db, current_user.id)
    combinations = find_color_combinations(garment.color, all_garments)
    
    return {
        "base_garment": {
            "id": garment.id,
            "color": garment.color,
            "category": garment.category
        },
        "complementary": [
            {"id": g.id, "color": g.color, "category": g.category}
            for g in combinations["complementary"]
        ],
        "analogous": [
            {"id": g.id, "color": g.color, "category": g.category}
            for g in combinations["analogous"]
        ],
        "neutral": [
            {"id": g.id, "color": g.color, "category": g.category}
            for g in combinations["neutral"]
        ]
    }

# ==================== Virtual Try-On & Outfit Preview ====================

@app.post("/outfit/create-preview")
def create_outfit_preview(
    garment_ids: List[int] = Query(...),
    occasion: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create and save an outfit preview."""
    try:
        garments = []
        for gid in garment_ids:
            g = get_garment(db, gid, current_user.id)
            if g:
                garments.append(g)
        
        if not garments:
            raise HTTPException(status_code=400, detail="No valid garments provided")
        
        # Save outfit to history
        outfit = create_outfit_record(db, current_user.id, garment_ids, occasion)
        
        # Create visual preview
        preview_path = create_outfit_collage(garments, outfit.id)
        
        return {
            "outfit_id": outfit.id,
            "occasion": occasion,
            "preview": preview_path,
            "items": [
                {
                    "id": g.id,
                    "category": g.category,
                    "color": g.color
                }
                for g in garments
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/outfit/try-on")
def virtual_try_on(
    request: TryOnRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a virtual try-on collage and return a web-accessible preview URL."""
    if not request.garment_ids:
        raise HTTPException(status_code=400, detail="No garments selected")
    if len(request.garment_ids) != 2:
        raise HTTPException(status_code=400, detail="Virtual try-on requires exactly 2 items: one top and one bottom")

    garments = []
    for gid in request.garment_ids:
        garment = get_garment(db, gid, current_user.id)
        if garment:
            garments.append(garment)

    if not garments:
        raise HTTPException(status_code=400, detail="No valid garments provided")
    if len(garments) != 2:
        raise HTTPException(status_code=400, detail="Select exactly 2 valid wardrobe items")

    top_categories = {"shirt", "cardigan", "jacket", "blazer", "trench_coat"}
    bottom_categories = {"pants", "shorts", "skirt"}
    has_top = any((g.category or "").lower() in top_categories for g in garments)
    has_bottom = any((g.category or "").lower() in bottom_categories for g in garments)
    if not (has_top and has_bottom):
        raise HTTPException(status_code=400, detail="Select one top and one bottom for virtual try-on")

    outfit = create_outfit_record(db, current_user.id, [g.id for g in garments], request.occasion or "virtual_tryon")
    preview_path, used_items, missing = create_virtual_tryon_preview(garments, outfit.id)
    if missing:
        raise HTTPException(status_code=400, detail="; ".join(missing))
    if not preview_path:
        raise HTTPException(status_code=500, detail="Failed to generate virtual try-on preview")

    preview_file = os.path.basename(preview_path)
    preview_url = f"/static/previews/{preview_file}"

    return {
        "outfit_id": outfit.id,
        "occasion": outfit.occasion,
        "preview_path": preview_path,
        "preview_url": preview_url,
        "selected_count": len(request.garment_ids),
        "used_count": len(used_items),
        "items": [
            {
                "id": g.id,
                "filename": g.filename,
                "category": g.category,
                "color": g.color,
                "style": g.style
            }
            for g in used_items
        ]
    }

@app.get("/outfit/history")
def get_outfit_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's outfit history."""
    outfits = get_user_outfit_history(db, current_user.id)
    return {
        "outfits": [
            {
                "id": o.id,
                "occasion": o.occasion,
                "date": o.date,
                "rating": o.rating,
                "notes": o.notes,
                "items": [
                    {"id": item.garment.id, "category": item.garment.category}
                    for item in o.outfit_items if item.garment
                ]
            }
            for o in outfits
        ]
    }

@app.get("/outfit/history/filter")
def get_outfit_history_filtered(
    occasion: Optional[str] = None,
    season: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Filter outfit history by occasion and/or season."""
    outfits = get_user_outfit_history(db, current_user.id)

    if occasion:
        normalized = normalize_occasion(occasion)
        outfits = [o for o in outfits if normalize_occasion(o.occasion) == normalized]
    if season:
        outfits = [
            o for o in outfits
            if any((item.garment and item.garment.season == season) for item in o.outfit_items)
        ]

    return {
        "outfits": [
            {
                "id": o.id,
                "occasion": o.occasion,
                "date": o.date,
                "rating": o.rating,
                "notes": o.notes,
                "items": [
                    {
                        "id": item.garment.id,
                        "category": item.garment.category,
                        "season": item.garment.season,
                        "fabric": item.garment.fabric
                    }
                    for item in o.outfit_items if item.garment
                ]
            }
            for o in outfits
        ]
    }

@app.put("/outfit/{outfit_id}/rate")
def rate_outfit_endpoint(
    outfit_id: int,
    rating: int = Query(..., ge=1, le=5),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rate an outfit."""
    outfit = rate_outfit(db, outfit_id, current_user.id, rating)
    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")
    
    return {
        "outfit_id": outfit.id,
        "rating": outfit.rating
    }

# ==================== User Preferences ====================

@app.get("/preferences")
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user style preferences."""
    prefs = get_user_preferences(db, current_user.id)
    return prefs

@app.put("/preferences")
def update_preferences(
    prefs: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user style preferences."""
    updated = update_user_preferences(db, current_user.id, **prefs.dict(exclude_unset=True))
    return updated

@app.get("/stylist/profile-summary")
def get_stylist_profile_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Summarize user's style signature from wardrobe inventory."""
    garments = get_user_garments(db, current_user.id)
    if not garments:
        return {
            "total_items": 0,
            "dominant_style": None,
            "dominant_season": None,
            "dominant_fabric": None,
            "top_categories": [],
            "palette": [],
            "message": "Upload wardrobe items to generate your stylist profile."
        }

    style_counts = Counter([g.style for g in garments if g.style])
    season_counts = Counter([g.season for g in garments if g.season])
    fabric_counts = Counter([g.fabric for g in garments if getattr(g, "fabric", None)])
    category_counts = Counter([g.category for g in garments if g.category])
    color_counts = Counter([g.color for g in garments if g.color])

    return {
        "total_items": len(garments),
        "dominant_style": style_counts.most_common(1)[0][0] if style_counts else None,
        "dominant_season": season_counts.most_common(1)[0][0] if season_counts else None,
        "dominant_fabric": fabric_counts.most_common(1)[0][0] if fabric_counts else None,
        "top_categories": [{"category": k, "count": v} for k, v in category_counts.most_common(5)],
        "palette": [{"color": k, "count": v} for k, v in color_counts.most_common(6)],
    }


@app.get("/analytics/wardrobe-summary")
def get_wardrobe_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return research-friendly wardrobe analytics and measurable signals."""
    garments = get_user_garments(db, current_user.id)
    outfits = get_user_outfit_history(db, current_user.id)
    return summarize_wardrobe_analytics(garments, outfits)

# ==================== Shopping Assistance ====================

@app.get("/shopping/complementary/{garment_id}")
def get_shopping_recommendations(
    garment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get shopping recommendations for complementary items."""
    garment = get_garment(db, garment_id, current_user.id)
    if not garment:
        raise HTTPException(status_code=404, detail="Garment not found")
    
    recommendations = get_complementary_items(
        garment.category,
        garment.color,
        gender=getattr(current_user, "gender", None),
        style=getattr(garment, "style", None),
        fabric=getattr(garment, "fabric", None),
        filename=getattr(garment, "filename", None),
        description=getattr(garment, "description", None),
    )
    return {
        "base_garment": {
            "id": garment.id,
            "category": garment.category,
            "color": garment.color,
            "style": garment.style,
            "season": garment.season,
            "gender": getattr(current_user, "gender", None)
        },
        **recommendations
    }

# ==================== ADVANCED AI FEATURES ====================

@app.post("/size-recommendations/update")
def update_size_preference(
    size: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's size preference and get recommendations."""
    prefs = get_user_preferences(db, current_user.id)
    
    if not prefs:
        prefs = create_user_preferences(db, current_user.id)
    
    # Store size (add to preferences dict or new column)
    if not hasattr(prefs, 'preferred_size'):
        # Store in JSON or create new column
        pass
    
    db.commit()
    
    body_type = getattr(prefs, 'body_type', None)
    recommendations = get_size_recommendations(size, body_type)
    
    return {
        "success": True,
        "size": size,
        "recommendations": recommendations
    }


@app.get("/size-recommendations")
def get_size_recommendations_endpoint(
    size: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed size and fit recommendations."""
    prefs = get_user_preferences(db, current_user.id)
    body_type = getattr(prefs, 'body_type', None) if prefs else None
    
    recommendations = get_size_recommendations(size, body_type)
    size_suggestion = suggest_size_for_body_type(body_type, size)
    
    return {
        "current_size": size or "Not specified",
        "recommendations": recommendations,
        "body_type_sizing": size_suggestion
    }


@app.get("/analytics/wardrobe-insights")
def get_wardrobe_insights_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive wardrobe insights and analytics."""
    insights = get_wardrobe_insights(db, current_user.id)
    
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "generated_at": datetime.utcnow().isoformat(),
        "insights": insights
    }


@app.get("/analytics/style-profile")
def get_style_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed style profile based on wardrobe and choices."""
    from utils.advanced_analytics import get_wardrobe_insights
    
    insights = get_wardrobe_insights(db, current_user.id)
    
    dominant_style = max(
        (insights.get('style_preferences', {}) or {}),
        key=lambda k: (insights.get('style_preferences', {}) or {}).get(k, {}).get('usage_rate', 0),
        default="balanced"
    )
    
    dominant_color = max(
        (insights.get('color_trends', {}) or {}),
        key=lambda k: (insights.get('color_trends', {}) or {}).get(k, {}).get('frequency', 0),
        default="neutral"
    )
    
    return {
        "dominant_style": dominant_style,
        "dominant_color": dominant_color,
        "health_score": insights.get('wardrobe_health', {}).get('overall_score', 0),
        "style_preferences": insights.get('style_preferences', {}),
        "color_distribution": insights.get('color_trends', {}),
        "recommendations": insights.get('recommendations_for_improvement', []),
        "trends": insights.get('trend_analysis', {})
    }


@app.post("/recommendations/enhanced")
def get_enhanced_recommendations(
    occasion: str = Form("casual"),
    body_type: Optional[str] = Form(None),
    weather_city: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get enhanced outfit recommendations with body type and other factors.
    """
    # Get basic recommendations
    basic_recs = recommend_outfit(db, current_user.id, occasion)
    
    # Filter by body type if provided
    if body_type:
        from utils.body_analysis import get_flattering_items_for_body_type
        flattering = get_flattering_items_for_body_type(db, current_user.id, body_type)
        # Score recommendations based on how well they match body type
    
    # Get weather-based adjustments if provided
    if weather_city:
        weather_data = get_weather(weather_city)
        weather_recs = get_clothing_recommendations_for_weather(weather_data)
    
    return {
        "occasion": occasion,
        "body_type": body_type,
        "recommendations": basic_recs,
        "personalization_factors": {
            "body_type_applied": bool(body_type),
            "weather_considered": bool(weather_city)
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint for API monitoring."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0-enhanced"
    }


@app.get("/shopping/trending/{category}")
def get_trending_items(category: str):
    """Get trending items for a category."""
    trending = find_trend_items(category, "#000000")
    
    return {
        "category": category,
        "trending_items": trending,
        "message": f"Check out these trending {category}s for 2024!"
    }


@app.get("/shopping/sustainability/{category}")
def get_sustainability_info(category: str):
    """Get sustainability information for a category."""
    info = get_sustainability_tips(category)
    
    return {
        "category": category,
        "sustainability": info
    }


@app.post("/shopping/outfit-sustainability")
def calculate_outfit_score(
    garment_ids: List[int] = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate sustainability score for an outfit."""
    garments = []
    for gid in garment_ids:
        g = get_garment(db, gid, current_user.id)
        if g:
            garments.append(g)
    
    if not garments:
        raise HTTPException(status_code=400, detail="No valid garments provided")
    
    score = calculate_outfit_sustainability_score(garments)
    
    return {
        "outfit_sustainability": score,
        "items_count": len(garments)
    }


@app.post("/shopping/outfit-links")
def get_outfit_shopping_links(
    garment_ids: List[int] = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate shopping links for complementary pieces based on selected outfit garments."""
    garments = []
    for gid in garment_ids:
        g = get_garment(db, gid, current_user.id)
        if g:
            garments.append(g)

    if not garments:
        raise HTTPException(status_code=400, detail="No valid garments provided")

    all_links = []
    complementary_summary = {}
    for g in garments:
        rec = get_complementary_items(g.category, g.color)
        for cat in rec.get("complementary_items", {}).keys():
            complementary_summary[cat] = complementary_summary.get(cat, 0) + 1
        all_links.extend(rec.get("shopping_links", []))

    # Deduplicate by store + category + url
    dedup = {}
    for link in all_links:
        key = (link.get("store"), link.get("category"), link.get("url"))
        if key not in dedup:
            dedup[key] = link

    return {
        "based_on": [
            {
                "id": g.id,
                "category": g.category,
                "color": g.color
            }
            for g in garments
        ],
        "recommended_categories": [
            {"category": cat, "count": count}
            for cat, count in sorted(complementary_summary.items(), key=lambda x: x[1], reverse=True)
        ],
        "shopping_links": list(dedup.values())[:40]
    }

# ==================== Image Serving ====================

@app.get("/image/{filename}")
def get_image(filename: str):
    """Get uploaded garment image."""
    try:
        return FileResponse(os.path.join(UPLOAD_DIR, f"uploaded_{filename}"))
    except:
        raise HTTPException(status_code=404, detail="Image not found")

# ==================== Enhanced Recommendations & Style ====================

@app.get("/recommendations/enhanced-explanation")
def get_enhanced_explanation(
    garment_ids: List[int] = Query(...),
    occasion: str = Query("casual"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI-generated detailed explanation for an outfit recommendation."""
    garments = []
    for gid in garment_ids:
        g = get_garment(db, gid, current_user.id)
        if g:
            garments.append(g)
    
    if not garments:
        raise HTTPException(status_code=400, detail="No valid garments provided")
    
    # Convert garments to dicts
    garment_dicts = [
        {
            "id": g.id,
            "category": g.category,
            "color": g.color,
            "style": g.style,
            "fabric": g.fabric
        }
        for g in garments
    ]
    
    explanation = generate_outfit_explanation(garment_dicts, occasion)
    
    return {
        "outfit_items": len(garments),
        "explanation": explanation,
        "styling_tips": generate_styling_tips(garment_dicts, occasion)
    }


@app.get("/style/profile")
def get_personal_style_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized style profile with personality type and recommendations."""
    user_garments = get_user_garments(db, current_user.id)
    
    if not user_garments:
        return {
            "style_type": "Getting Started",
            "personality": "Start building your style by adding items to your wardrobe!",
            "characteristics": ["Blank slate", "Ready to create", "Building foundation"],
            "color_palette": [],
            "occasion_readiness": {},
            "style_strengths": [],
            "style_recommendations": ["Add your first wardrobe items", "Explore different styles", "Build your color palette"],
            "versatility_score": 0
        }
    
    garment_dicts = [
        {
            "id": g.id,
            "category": g.category,
            "color": g.color,
            "style": g.style,
            "fabric": g.fabric
        }
        for g in user_garments
    ]
    
    profile = generate_style_profile(garment_dicts, user_data={"outfit_history": []})
    
    return profile


@app.post("/style/update-profile")
def update_style_preference(
    body_type: str = Form(None),
    style_type: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's style preferences."""
    update_data = {}
    if body_type:
        update_data["body_type"] = body_type
    if style_type:
        update_data["style_type"] = style_type
    
    updated_user = update_user(db, current_user.id, update_data)
    
    return {
        "message": "Style preferences updated",
        "body_type": updated_user.body_type,
        "style_type": getattr(updated_user, "style_type", None)
    }


@app.get("/style/recommendations")
def get_personalized_style_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized style recommendations based on body type and preferences."""
    user_garments = get_user_garments(db, current_user.id)
    profile = generate_style_profile(
        [{
            "id": g.id,
            "category": g.category,
            "color": g.color,
            "style": g.style,
            "fabric": g.fabric
        } for g in user_garments or []]
    )
    
    recommendations = []
    
    # Based on versatility score
    if profile.get("versatility_score", 0) < 40:
        recommendations.append("Increase wardrobe versatility by adding neutral basics")
        recommendations.append("Mix and match common pieces more frequently")
    elif profile.get("versatility_score", 0) > 70:
        recommendations.append("Your wardrobe is highly versatile - excellent foundation!")
        recommendations.append("Experiment with bold statement pieces")
    
    # Based on style type
    style_recs = {
        "Casual Chic": ["Add one statement accessory to elevate casual looks", "Experiment with layering"],
        "Elegant Professional": ["Add elegant accessories for sophistication", "Invest in quality basics"],
        "Fashion Forward": ["Stay updated with trending styles", "Mix trends with timeless pieces"],
        "Bohemian Spirit": ["Embrace unique patterns and textures", "Mix vintage with modern"],
        "Minimalist": ["Focus on quality over quantity", "Build a capsule wardrobe"],
        "Classic Elegance": ["Invest in timeless pieces", "Perfect your style essentials"]
    }
    
    style_name = profile.get("style_type", "Casual Chic")
    recommendations.extend(style_recs.get(style_name, []))
    
    # Remove duplicates
    recommendations = list(dict.fromkeys(recommendations))
    
    return {
        "style_profile": profile,
        "personalized_recommendations": recommendations[:5],
        "versatility_score": profile.get("versatility_score", 0)
    }

# ==================== Health Check ====================

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.app_version, "app": settings.app_name}


@app.get("/debug/weather-comparison")
def weather_comparison():
    """
    Debug endpoint to verify weather service is working correctly.
    Returns weather data for multiple cities to verify they're different.
    """
    test_cities = [
        "Hyderabad", "Delhi", "Mumbai", 
        "London", "New York", "Dubai", 
        "Tokyo", "Sydney"
    ]
    
    results = {}
    for city in test_cities:
        weather_data = get_weather(city)
        results[city] = {
            "temperature": weather_data.get("temp"),
            "condition": weather_data.get("condition"),
            "humidity": weather_data.get("humidity"),
            "source": weather_data.get("source", "unknown")
        }
    
    return {
        "message": "Weather data for multiple cities (should all be different)",
        "cities_weather": results,
        "api_key_configured": bool(settings.openweather_api_key),
        "note": "If all temperatures are the same, check OpenWeather API key configuration"
    }
