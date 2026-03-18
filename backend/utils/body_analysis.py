# backend/utils/body_analysis.py
"""Body type and personal measurement analysis for style recommendations."""

from typing import Dict, List, Optional
from models import Garment, OutfitHistory, OutfitItem
from sqlalchemy.orm import Session

def analyze_body_type(db: Session, user_id: int, body_type: Optional[str] = None) -> Dict:
    """
    Analyze user's body type based on outfit history or stored preferences.
    
    Body types: 
    - Apple: Larger midsection, smaller bottom
    - Pear: Larger bottom, smaller top
    - Hourglass: Balanced with curves
    - Rectangle: Equal top and bottom
    - Inverted Triangle: Larger top, smaller bottom
    """
    from crud import get_user_preferences
    
    prefs = get_user_preferences(db, user_id)
    
    if not body_type and prefs:
        body_type = getattr(prefs, 'body_type', None)
    
    return {
        "body_type": body_type or "Not specified",
        "recommendations": get_sizing_recommendations(body_type),
        "style_guide": get_style_guide_for_body_type(body_type),
        "flattering_items": get_flattering_items_for_body_type(db, user_id, body_type)
    }


def get_sizing_recommendations(body_type: Optional[str]) -> Dict:
    """Get sizing recommendations based on body type."""
    recommendations = {
        "apple": {
            "focus": "Flatter the midsection",
            "best_fits": ["A-line", "empire waist", "wrap dresses", "structured fabrics"],
            "avoid": ["Tight belts", "horizontal stripes on torso", "clingy materials"],
            "top_suggestions": "Peplum tops, tunics, structured blazers",
            "bottom_suggestions": "Straight leg, dark colors, structured fabrics"
        },
        "pear": {
            "focus": "Balance lower body",
            "best_fits": ["Wide leg pants", "A-line skirts", "lighter tops"],
            "avoid": ["Skinny jeans", "tight skirts", "horizontal stripes on hips"],
            "top_suggestions": "Bright colors, patterns, ruffles, crop tops",
            "bottom_suggestions": "Flared, A-line, structured, darker colors"
        },
        "hourglass": {
            "focus": "Emphasize curves",
            "best_fits": ["Fitted styles", "wrap dresses", "belted items"],
            "avoid": ["Oversized", "shapeless", "boxy cuts"],
            "top_suggestions": "Fitted tops, wrap styles, form-fitting",
            "bottom_suggestions": "Fitted jeans, pencil skirts, tailored pants"
        },
        "rectangle": {
            "focus": "Create curves",
            "best_fits": ["Ruching", "layering", "ruffles", "horizontal stripes"],
            "avoid": ["Straight cuts", "monochromatic looks"],
            "top_suggestions": "Ruffled, layered, patterned, fitted",
            "bottom_suggestions": "Pleated, A-line, cargo, patterned"
        },
        "inverted_triangle": {
            "focus": "Balance shoulders",
            "best_fits": ["A-line skirts", "bootcut jeans", "flared bottoms"],
            "avoid": ["Shoulder details", "horizontal stripes on shoulders"],
            "top_suggestions": "Neutral colors, simple cuts, strapless",
            "bottom_suggestions": "Flared, bright colors, patterns, wide leg"
        }
    }
    
    body_type_key = body_type.lower().replace(" ", "_").replace("-", "_") if body_type else ""
    return recommendations.get(body_type_key, recommendations.get("rectangle", {}))


def get_style_guide_for_body_type(body_type: Optional[str]) -> List[str]:
    """Get detailed style guide for a specific body type."""
    guides = {
        "apple": [
            "✓ Wear structured fabrics to smooth your midsection",
            "✓ Choose darker colors for your core area",
            "✓ Opt for empire waist and A-line cuts",
            "✓ Layer with open cardigans for added definition",
            "✓ Avoid tight belts and clingy fabrics"
        ],
        "pear": [
            "✓ Balance your lower body with wider tops",
            "✓ Use bright colors and patterns on top",
            "✓ Go for darker shades on bottom",
            "✓ Try A-line skirts and flared jeans",
            "✓ Add details like ruffles to tops"
        ],
        "hourglass": [
            "✓ Emphasize your natural curves with fitted styles",
            "✓ Belted items highlight your waist",
            "✓ Wrap dresses are your best friend",
            "✓ Fitted jeans and tailored pants look amazing",
            "✓ Show off your shape with your clothing"
        ],
        "rectangle": [
            "✓ Create curves with ruffles and layering",
            "✓ Use horizontal stripes and patterns",
            "✓ Try ruching and gathering details",
            "✓ Pleated skirts and cargo pants add dimension",
            "✓ Peplum tops and cropped styles work well"
        ],
        "inverted_triangle": [
            "✓ Balance shoulders with wide bottoms",
            "✓ Keep shoulders simple and clean",
            "✓ Choose A-line and flared skirts",
            "✓ Add color and pattern to bottoms",
            "✓ Strapless or simple necklines work best"
        ]
    }
    
    body_type_key = body_type.lower().replace(" ", "_").replace("-", "_") if body_type else ""
    return guides.get(body_type_key, [
        "✓ Understanding your body type helps with better style choices",
        "✓ Focus on what makes you feel confident",
        "✓ Experiment with different cuts and styles"
    ])


def get_flattering_items_for_body_type(db: Session, user_id: int, body_type: Optional[str]) -> Dict:
    """Find flattering items from user's wardrobe based on body type."""
    from crud import get_user_garments
    
    garments = get_user_garments(db, user_id) or []
    flattering_tops = []
    flattering_bottoms = []
    flattering_dresses = []
    
    body_type_key = body_type.lower().replace(" ", "_") if body_type else ""
    
    good_styles = {
        "apple": {"top": ["cardigan", "tunic"], "bottom": ["wide", "straight"]},
        "pear": {"top": ["crop", "peplum"], "bottom": ["wide", "a-line"]},
        "hourglass": {"top": ["fitted", "wrap"], "bottom": ["fitted", "pencil"]},
        "rectangle": {"top": ["ruffled", "peplum"], "bottom": ["flared", "a-line"]},
        "inverted_triangle": {"top": ["simple"], "bottom": ["flared", "wide"]}
    }
    
    good_attrs = good_styles.get(body_type_key, {})
    
    for garment in garments:
        category = (garment.category or "").lower()
        style = (garment.style or "").lower()
        
        if any(cat in category for cat in ["top", "shirt", "cardigan", "jacket", "blouse"]):
            if good_attrs.get("top"):
                if any(s in style for s in good_attrs["top"]):
                    flattering_tops.append(garment.filename)
        elif any(cat in category for cat in ["bottom", "pants", "skirt"]):
            if good_attrs.get("bottom"):
                if any(s in style for s in good_attrs["bottom"]):
                    flattering_bottoms.append(garment.filename)
        elif "dress" in category:
            flattering_dresses.append(garment.filename)
    
    return {
        "flattering_tops": flattering_tops[:5],
        "flattering_bottoms": flattering_bottoms[:5],
        "flattering_dresses": flattering_dresses[:5]
    }


def calculate_body_type_score(db: Session, user_id: int) -> Dict:
    """Calculate body type confidence score based on user preferences and wardrobe analysis."""
    from crud import get_user_outfit_history, get_user_preferences
    
    outfits = get_user_outfit_history(db, user_id) or []
    prefs = get_user_preferences(db, user_id)
    body_type = getattr(prefs, 'body_type', None) if prefs else None
    
    # Base confidence from body type preference
    if body_type:
        base_confidence = 70  # If user specified body type
    else:
        base_confidence = 40  # If body type not specified
    
    # Boost confidence with outfit history
    if outfits:
        # Each outfit adds to confidence (up to 30% additional)
        outfit_boost = min(30, len(outfits) * 3)
        confidence = min(100, base_confidence + outfit_boost)
        analysis = f"Based on {len(outfits)} saved outfits and your preferences."
    else:
        confidence = base_confidence
        analysis = "Confidence based on your profile. Save outfits to improve analysis."
    
    return {
        "confidence": round(confidence),
        "analysis": analysis
    }
