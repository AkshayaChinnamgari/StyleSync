# backend/utils/size_recommendations.py
"""Size and fit recommendations based on body measurements and preferences."""

from typing import Dict, List, Optional


def get_size_recommendations(size: Optional[str], body_type: Optional[str]) -> Dict:
    """
    Get size recommendations and fit guidelines.
    
    Args:
        size: Current size (XS, S, M, L, XL, XXL)
        body_type: User's body type for personalized advice
    """
    size_guides = {
        "XS": {
            "fit_tips": [
                "Look for petite or cropped styles",
                "Avoid oversized and volume",
                "Vertical stripes elongate your frame",
                "Fitted styles work best"
            ],
            "alternatives": ["S", "Children's XL"],
            "brands_known_for_xs": ["ASOS Petite", "H&M", "Zara", "Forever 21"]
        },
        "S": {
            "fit_tips": [
                "Petite-fit jeans and dresses work well",
                "Avoid excess fabric and drowning in clothes",
                "Cropped items can be flattering",
                "Look for fitted silhouettes"
            ],
            "alternatives": ["XS", "M"],
            "brands_known_for_s": ["ASOS", "Zara", "H&M", "Forever 21", "Uniqlo"]
        },
        "M": {
            "fit_tips": [
                "Most versatile size",
                "Fitted and relaxed styles both work",
                "Try oversized looks with layering",
                "Tailoring can perfect the fit"
            ],
            "alternatives": ["S", "L"],
            "brands_known_for_m": ["Gap", "H&M", "Uniqlo", "Everlane", "J.Crew"]
        },
        "L": {
            "fit_tips": [
                "Structured fabrics work best",
                "Dark colors can be slimming",
                "Vertical lines elongate",
                "Fitted styles flatter more than loose"
            ],
            "alternatives": ["M", "XL"],
            "brands_known_for_l": ["H&M", "Zara", "Gap", "Old Navy", "Target"]
        },
        "XL": {
            "fit_tips": [
                "Focus on structured and quality fabrics",
                "Monochromatic looks are streamlined",
                "Layering adds interest",
                "Well-fitted beats oversized"
            ],
            "alternatives": ["L", "XXL"],
            "brands_known_for_xl": ["Torrid", "Old Navy", "H&M", "Gap", "Uniqlo"]
        },
        "XXL": {
            "fit_tips": [
                "Quality fabrics are key",
                "Structured silhouettes flatter",
                "Vertical stripes and seams work",
                "Proper tailoring makes all the difference"
            ],
            "alternatives": ["XL"],
            "brands_known_for_xxl": ["Torrid", "Lane Bryant", "Old Navy", "H&M Plus"]
        }
    }
    
    base_guide = size_guides.get(size or "M", size_guides["M"])
    
    return {
        "size": size or "M",
        "fit_tips": base_guide["fit_tips"],
        "alternatives": base_guide["alternatives"],
        "recommended_brands": base_guide["brands_known_for_" + (size or "M").lower()],
        "personalized_advice": get_personalized_size_advice(size, body_type)
    }


def get_personalized_size_advice(size: Optional[str], body_type: Optional[str]) -> List[str]:
    """Generate personalized size and fit advice based on combination of factors."""
    advice = []
    
    if body_type:
        body_advice = {
            "apple": [
                "Choose tops that don't cling to your midsection",
                "Look for empire waist or wrap styles",
                "Consider going up a size in fitted tops for comfort",
                "A-line styles work better than bodycon"
            ],
            "pear": [
                "You might need different sizes for tops vs bottoms",
                "Try sizing up in bottoms for comfort",
                "Tops can be more fitted since your upper body is smaller",
                "Look for flared or bootcut options"
            ],
            "hourglass": [
                "Sizing is usually standard across the board",
                "Fitted styles show off your curves beautifully",
                "Don't size up to hide your shape",
                "Wrap and belt styles are your best friends"
            ],
            "rectangle": [
                "Look for structured fabrics that add dimension",
                "Peplum and ruffle details add curves",
                "Standard sizing usually works well",
                "Layering creates interesting silhouettes"
            ],
            "inverted_triangle": [
                "You might size up in tops for shoulder comfort",
                "Look for simple, clean necklines",
                "Size down in bottoms to balance proportions",
                "A-line and flared styles work best"
            ]
        }
        
        body_key = body_type.lower().replace(" ", "_")
        advice.extend(body_advice.get(body_key, []))
    
    # Size-specific advice
    if size:
        size_specific = {
            "XS": "Petite-specific lines can save you money on alterations",
            "S": "You have great options available - maximize fitted styles",
            "M": "You have the most versatile size - experiment freely",
            "L": "Focus on fit over size - quality tailoring makes all the difference",
            "XL": "Structured fabrics and good fit are your investment priorities",
            "XXL": "Find brands that specialize in your size for better fits"
        }
        if size in size_specific:
            advice.append(size_specific[size])
    
    return advice if advice else ["Try different styles to find what makes you feel confident"]


def get_fit_score(garment_category: str, body_type: Optional[str], size: Optional[str]) -> float:
    """
    Calculate expected fit score (0-1) for a garment given body type and size.
    Higher score = better expected fit.
    """
    base_score = 0.7  # Start with decent baseline
    
    body_fit_bonuses = {
        "apple": {
            "cardigan": 0.2,
            "tunic": 0.15,
            "wrap_dress": 0.2,
            "empire_waist": 0.15,
            "jacket": 0.1
        },
        "pear": {
            "wide_leg": 0.2,
            "a_line": 0.15,
            "flared": 0.15,
            "crop_top": 0.1,
            "peplum": 0.1
        },
        "hourglass": {
            "fitted": 0.2,
            "wrap": 0.2,
            "belt": 0.15,
            "pencil_skirt": 0.1,
            "bodycon": 0.1
        },
        "rectangle": {
            "ruffled": 0.15,
            "horizontal_stripe": 0.1,
            "peplum": 0.1,
            "a_line": 0.1,
            "layer": 0.1
        },
        "inverted_triangle": {
            "a_line": 0.15,
            "flared": 0.15,
            "bootcut": 0.1,
            "simple_top": 0.1,
            "strapless": 0.1
        }
    }
    
    if body_type:
        body_key = body_type.lower().replace(" ", "_")
        bonuses = body_fit_bonuses.get(body_key, {})
        
        category_key = garment_category.lower().replace(" ", "_")
        bonus = bonuses.get(category_key, 0)
        base_score = min(1.0, base_score + bonus)
    
    # Size-specific adjustments
    if size:
        size_score_map = {
            "XS": 0.95,
            "S": 0.97,
            "M": 1.0,
            "L": 0.95,
            "XL": 0.93,
            "XXL": 0.90
        }
        base_score *= size_score_map.get(size, 1.0)
    
    return round(base_score, 2)


def suggest_size_for_body_type(body_type: Optional[str], preferred_size: Optional[str]) -> Dict:
    """Suggest optimal sizing based on body type."""
    suggestions = {
        "apple": {
            "top_size": "One size fits most, focus on fit",
            "bottom_size": "One size fits most, prioritize structure",
            "advice": "Tops and bottoms should both be well-fitted but not clingy"
        },
        "pear": {
            "top_size": "Consider sizing down in tops",
            "bottom_size": "Consider sizing up in bottoms",
            "advice": "Mismatch in sizing is common for pear shapes"
        },
        "hourglass": {
            "top_size": "Standard sizing works well",
            "bottom_size": "Standard sizing works well",
            "advice": "Keep it consistent - don't hide your shape"
        },
        "rectangle": {
            "top_size": "Standard sizing works well",
            "bottom_size": "Standard sizing works well",
            "advice": "Focus on style details rather than size"
        },
        "inverted_triangle": {
            "top_size": "Consider sizing up for shoulder room",
            "bottom_size": "Consider sizing down for balance",
            "advice": "The size difference helps balance your proportions"
        }
    }
    
    body_key = body_type.lower().replace(" ", "_") if body_type else ""
    info = suggestions.get(body_key, suggestions["rectangle"])
    
    return {
        "body_type": body_type or "Not specified",
        "recommendations": info,
        "current_size": preferred_size or "Not specified",
        "fit_score": get_fit_score("general", body_type, preferred_size)
    }
