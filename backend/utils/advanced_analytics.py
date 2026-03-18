# backend/utils/advanced_analytics.py
"""Advanced analytics and insights for wardrobe analysis."""

from typing import Dict, List, Optional
from collections import Counter
from datetime import datetime, timedelta
from models import Garment, OutfitHistory, OutfitItem
from sqlalchemy.orm import Session
import statistics


def get_wardrobe_insights(db: Session, user_id: int) -> Dict:
    """Get comprehensive wardrobe insights and statistics."""
    from crud import get_user_garments, get_user_outfit_history
    
    garments = get_user_garments(db, user_id) or []
    outfits = get_user_outfit_history(db, user_id) or []
    
    return {
        "wardrobe_health": calculate_wardrobe_health(garments, outfits),
        "category_distribution": get_category_distribution(garments),
        "color_trends": get_color_trends(garments),
        "style_preferences": get_style_preferences(garments, outfits),
        "usage_stats": calculate_usage_stats(db, user_id, garments, outfits),
        "recommendations_for_improvement": get_wardrobe_recommendations(garments, outfits),
        "trend_analysis": analyze_trends(garments, outfits)
    }


def calculate_wardrobe_health(garments: List, outfits: List) -> Dict:
    """Calculate overall wardrobe health score (0-100)."""
    score = 50  # Base score
    
    # Item count bonus (20-100 items is ideal)
    item_count = len(garments)
    if 15 <= item_count <= 100:
        score += min(20, (item_count - 15) / 4.25)
    elif item_count > 100:
        score += 20
    
    # Outfit creation success rate
    if outfits:
        rated_outfits = [getattr(o, 'rating', 3) for o in outfits if getattr(o, 'rating', None)]
        if rated_outfits:
            avg_rating = statistics.mean(rated_outfits)
            rating_bonus = (avg_rating - 1) * 10
            score += min(15, rating_bonus)
    
    # Variety in categories
    if garments:
        categories = [g.category for g in garments]
        unique_categories = len(set(categories))
        category_bonus = min(15, unique_categories * 2)
        score += category_bonus
    
    # Color diversity
    if garments:
        colors = [g.color for g in garments if g.color]
        unique_colors = len(set(colors))
        color_bonus = min(10, unique_colors * 0.5)
        score += color_bonus
    
    score = min(100, score)
    
    return {
        "overall_score": round(score),
        "status": get_health_status(score),
        "items_count": item_count,
        "outfits_created": len(outfits),
        "recommendation": get_health_recommendation(score, item_count, len(outfits))
    }


def get_health_status(score: float) -> str:
    """Get health status label based on score."""
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Fair"
    else:
        return "Needs Work"


def get_health_recommendation(score: float, item_count: int, outfit_count: int) -> str:
    """Get recommendation to improve wardrobe health."""
    if item_count < 15:
        return "Build your wardrobe foundation with essential pieces"
    elif item_count > 150:
        return "Consider curating your wardrobe - quality over quantity"
    elif outfit_count < item_count * 0.1:
        return "Start creating outfits to better utilize your items"
    else:
        return "Your wardrobe is developing well!"


def get_category_distribution(garments: List) -> Dict:
    """Analyze distribution of clothing categories."""
    if not garments:
        return {}
    
    categories = [g.category or "Other" for g in garments]
    counter = Counter(categories)
    total = len(garments)
    
    distribution = {}
    for cat, count in counter.most_common():
        percentage = (count / total) * 100
        distribution[cat] = {
            "count": count,
            "percentage": round(percentage, 1),
            "status": get_category_status(cat, percentage)
        }
    
    return distribution


def get_category_status(category: str, percentage: float) -> str:
    """Get status for a category based on typical wardrobe distribution."""
    category_lower = category.lower()
    
    ideal_ranges = {
        "shirt": (25, 35),
        "pants": (20, 25),
        "dress": (10, 15),
        "shoes": (10, 15),
        "jacket": (5, 10),
        "accessories": (5, 10)
    }
    
    for key, (min_pct, max_pct) in ideal_ranges.items():
        if key in category_lower:
            if min_pct <= percentage <= max_pct:
                return "Balanced"
            elif percentage < min_pct:
                return "Under-represented"
            else:
                return "Over-represented"
    
    return "Specialty"


def get_color_trends(garments: List) -> Dict:
    """Analyze color preferences and trends in wardrobe."""
    if not garments:
        return {}
    
    colors = [g.color for g in garments if g.color]
    counter = Counter(colors)
    
    trends = {}
    for color, count in counter.most_common(10):
        trends[color] = {
            "frequency": count,
            "versatility": calculate_color_versatility(color),
            "recommendation": get_color_recommendation(color, count)
        }
    
    return trends


def calculate_color_versatility(color: str) -> str:
    """Rate color versatility."""
    color_lower = color.lower()
    
    if any(x in color_lower for x in ["black", "white", "gray", "navy", "beige"]):
        return "Highly Versatile"
    elif any(x in color_lower for x in ["blue", "green", "brown", "red"]):
        return "Versatile"
    else:
        return "Limited"


def get_color_recommendation(color: str, count: int) -> str:
    """Get recommendation for a color in wardrobe."""
    if count > 8:
        return "Well-represented, consider adding variety"
    elif count > 5:
        return "Good balance"
    elif count > 2:
        return "Build on this color"
    else:
        return "Emerging color"


def get_style_preferences(garments: List, outfits: List) -> Dict:
    """Analyze style preferences based on wardrobe and usage."""
    if not garments:
        return {}
    
    # Count styles in wardrobe
    wardrobe_styles = Counter([g.style or "casual" for g in garments])
    
    # Count styles used in popular outfits
    high_rated_styles = Counter()
    for outfit in outfits:
        if getattr(outfit, 'rating', None) and getattr(outfit, 'rating', 0) >= 4:
            for item in getattr(outfit, 'outfit_items', []):
                garment = getattr(item, 'garment', None)
                if garment:
                    high_rated_styles[garment.style or "casual"] += 1
    
    preferences = {}
    for style, count in wardrobe_styles.most_common():
        used = high_rated_styles.get(style, 0)
        usage_rate = (used / count * 100) if count > 0 else 0
        
        preferences[style] = {
            "wardrobe_count": count,
            "high_rated_usage": used,
            "usage_rate": round(usage_rate, 1),
            "recommendation": get_style_recommendation(style, usage_rate)
        }
    
    return preferences


def get_style_recommendation(style: str, usage_rate: float) -> str:
    """Get recommendation for a style."""
    if usage_rate > 50:
        return "This is your signature style - excellent choice"
    elif usage_rate > 25:
        return "You wear this style regularly"
    elif usage_rate > 10:
        return "Occasional wear"
    else:
        return f"Try wearing your {style} items more often"


def calculate_usage_stats(db: Session, user_id: int, garments: List, outfits: List) -> Dict:
    """Calculate garment usage statistics."""
    from models import OutfitItem
    
    if not garments:
        return {"average_usage": 0, "most_used": [], "least_used": []}
    
    # Calculate usage count for each garment
    usage_data = []
    for garment in garments:
        count = db.query(OutfitItem).filter(OutfitItem.garment_id == garment.id).count()
        usage_data.append((garment.filename or garment.id, count))
    
    if usage_data:
        avg_usage = statistics.mean([count for _, count in usage_data])
        most_used = sorted(usage_data, key=lambda x: x[1], reverse=True)[:5]
        least_used = sorted(usage_data, key=lambda x: x[1])[:5]
    else:
        avg_usage = 0
        most_used = []
        least_used = []
    
    return {
        "average_usage_per_item": round(avg_usage, 1),
        "most_used_items": [{"item": item, "times_worn": count} for item, count in most_used],
        "least_used_items": [{"item": item, "times_worn": count} for item, count in least_used],
        "wardrobe_utilization": round((sum(1 for _, count in usage_data if count > 0) / len(garments) * 100)) if garments else 0
    }


def get_wardrobe_recommendations(garments: List, outfits: List) -> List[str]:
    """Generate specific recommendations to improve wardrobe."""
    recommendations = []
    
    categories = [g.category or "Other" for g in garments]
    category_counts = Counter(categories)
    
    # Category recommendations
    if category_counts.get("pants", 0) < 3:
        recommendations.append("Add more bottoms - aim for 3-5 pairs")
    if category_counts.get("shirt", 0) < 5:
        recommendations.append("Build your top collection - it's the foundation of any wardrobe")
    if category_counts.get("jacket", 0) < 2:
        recommendations.append("Add a versatile jacket for layering and occasion variety")
    
    # Color recommendations
    colors = [g.color for g in garments if g.color]
    unique_colors = len(set(colors))
    if unique_colors < 5:
        recommendations.append("Add more color variety to your wardrobe")
    
    # Outfit generation recommendation
    if len(outfits) < len(garments) * 0.1:
        recommendations.append(f"Try creating {len(garments) // 2} more outfits to explore combinations")
    
    if not recommendations:
        recommendations = ["Your wardrobe is well-balanced!", "Focus on adding pieces you love"]
    
    return recommendations


def analyze_trends(garments: List, outfits: List) -> Dict:
    """Analyze emerging trends in wardrobe choices."""
    if not outfits:
        return {"trend": "Not enough data", "details": "Create more outfits to identify trends"}
    
    # Analyze recent outfits (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_outfits = [o for o in outfits if (o.date if hasattr(o, 'date') else datetime.utcnow()) > thirty_days_ago]
    
    if recent_outfits:
        recent_styles = Counter([g.style for o in recent_outfits for item in getattr(o, 'outfit_items', []) 
                                for g in [getattr(item, 'garment', None)] if g])
        dominant_recent = recent_styles.most_common(1)
        
        if dominant_recent:
            return {
                "trend": f"Recently favoring {dominant_recent[0][0]} style",
                "frequency": dominant_recent[0][1],
                "insight": "You're gravitating toward this style - consider adding more items in this direction"
            }
    
    return {
        "trend": "Exploring multiple styles",
        "insight": "Great variety in your choices!"
    }
