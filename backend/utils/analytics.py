from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional

from models import Garment, OutfitHistory
from services.shopping import calculate_outfit_sustainability_score
from utils.recommend import get_color_harmony_score, normalize_occasion, score_candidate


TOP_CATEGORIES = {"shirt", "cardigan", "jacket", "blazer", "trench_coat", "kurta"}
BOTTOM_CATEGORIES = {"pants", "shorts", "skirt"}
FOOTWEAR_CATEGORIES = {"shoes", "boots", "sandals"}
ACCESSORY_CATEGORIES = {"necklace", "bracelet", "earrings", "watch", "hat", "gloves", "scarf", "belt", "bag"}

OCCASION_TEMPLATES = {
    "casual": {"shirt", "pants", "shoes"},
    "formal": {"dress", "shoes"},
    "professional": {"shirt", "pants", "shoes"},
    "party": {"dress", "shoes"},
    "weekend": {"shirt", "pants", "shoes"},
    "travel": {"shirt", "pants", "shoes", "jacket"},
    "interview": {"shirt", "pants", "blazer", "shoes"},
    "date": {"dress", "shoes"},
}


def _pct(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((count / total) * 100, 1)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return round(max(low, min(high, value)), 1)


def _normalize_category(category: Optional[str]) -> str:
    token = (category or "").strip().lower()
    aliases = {
        "tshirt": "shirt",
        "t-shirt": "shirt",
        "tee": "shirt",
        "top": "shirt",
        "trousers": "pants",
        "jeans": "pants",
        "sneaker": "shoes",
        "heels": "shoes",
        "loafer": "shoes",
        "coat": "trench_coat",
    }
    return aliases.get(token, token)


def _bucket_categories(garments: List[Garment]) -> Dict[str, int]:
    counts = {"tops": 0, "bottoms": 0, "footwear": 0, "accessories": 0, "dresses": 0, "outerwear": 0}
    outerwear_categories = {"jacket", "blazer", "trench_coat", "cardigan"}
    for garment in garments:
        category = _normalize_category(getattr(garment, "category", None))
        if category in TOP_CATEGORIES:
            counts["tops"] += 1
        if category in BOTTOM_CATEGORIES:
            counts["bottoms"] += 1
        if category in FOOTWEAR_CATEGORIES:
            counts["footwear"] += 1
        if category in ACCESSORY_CATEGORIES:
            counts["accessories"] += 1
        if category == "dress":
            counts["dresses"] += 1
        if category in outerwear_categories:
            counts["outerwear"] += 1
    return counts


def _build_gap_analysis(garments: List[Garment]) -> List[Dict]:
    bucket_counts = _bucket_categories(garments)
    gap_targets = {
        "tops": 3,
        "bottoms": 3,
        "footwear": 2,
        "accessories": 2,
        "outerwear": 1,
    }
    gaps = []
    for key, target in gap_targets.items():
        current = bucket_counts.get(key, 0)
        if current < target:
            gaps.append({
                "area": key,
                "current": current,
                "target": target,
                "severity": "high" if current == 0 else "medium",
                "recommendation": f"Add {max(1, target - current)} more {key} piece(s) to improve outfit coverage.",
            })
    return gaps


def _occasion_readiness(garments: List[Garment]) -> List[Dict]:
    wardrobe_categories = {_normalize_category(getattr(g, "category", None)) for g in garments}
    readiness = []
    for occasion, required in OCCASION_TEMPLATES.items():
        matched = len(required.intersection(wardrobe_categories))
        score = _pct(matched, len(required))
        missing = sorted(required.difference(wardrobe_categories))
        readiness.append({
            "occasion": occasion,
            "score": score,
            "missing_categories": missing,
            "ready": score >= 66.0,
        })
    return sorted(readiness, key=lambda item: item["score"], reverse=True)


def _usage_metrics(garments: List[Garment], outfits: List[OutfitHistory]) -> Dict:
    usage_counter = Counter()
    occasion_counter = Counter()
    rating_values = []

    for outfit in outfits:
        normalized = normalize_occasion(getattr(outfit, "occasion", "") or "")
        if normalized:
            occasion_counter[normalized] += 1
        if getattr(outfit, "rating", None) is not None:
            rating_values.append(outfit.rating)
        for outfit_item in getattr(outfit, "outfit_items", []) or []:
            garment = getattr(outfit_item, "garment", None)
            if garment and getattr(garment, "id", None):
                usage_counter[garment.id] += 1

    total_garments = len(garments)
    worn_items = len(usage_counter)
    unworn_items = max(0, total_garments - worn_items)
    average_rating = round(sum(rating_values) / len(rating_values), 2) if rating_values else None

    most_used = []
    garment_lookup = {g.id: g for g in garments if getattr(g, "id", None)}
    for garment_id, count in usage_counter.most_common(5):
        garment = garment_lookup.get(garment_id)
        if garment:
            most_used.append({
                "id": garment.id,
                "filename": garment.filename,
                "category": garment.category,
                "color": garment.color,
                "count": count,
            })

    return {
        "outfits_logged": len(outfits),
        "worn_items": worn_items,
        "unworn_items": unworn_items,
        "usage_coverage": _pct(worn_items, total_garments),
        "average_rating": average_rating,
        "favorite_occasions": [{"occasion": k, "count": v} for k, v in occasion_counter.most_common(5)],
        "most_used_items": most_used,
    }


def summarize_wardrobe_analytics(garments: List[Garment], outfits: List[OutfitHistory]) -> Dict:
    if not garments:
        return {
            "total_items": 0,
            "category_distribution": [],
            "style_distribution": [],
            "season_distribution": [],
            "palette": [],
            "readiness": [],
            "gaps": [],
            "usage": {
                "outfits_logged": len(outfits),
                "worn_items": 0,
                "unworn_items": 0,
                "usage_coverage": 0.0,
                "average_rating": None,
                "favorite_occasions": [],
                "most_used_items": [],
            },
            "scores": {
                "wardrobe_balance": 0.0,
                "seasonal_coverage": 0.0,
                "versatility": 0.0,
                "sustainability": 0.0,
            },
            "insights": [
                "No wardrobe data yet.",
                "Upload garments to unlock readiness, balance, and sustainability metrics.",
            ],
        }

    total_items = len(garments)
    category_counts = Counter([_normalize_category(getattr(g, "category", None)) for g in garments if getattr(g, "category", None)])
    style_counts = Counter([(getattr(g, "style", None) or "").lower() for g in garments if getattr(g, "style", None)])
    season_counts = Counter([(getattr(g, "season", None) or "").lower() for g in garments if getattr(g, "season", None)])
    color_counts = Counter([(getattr(g, "color", None) or "").lower() for g in garments if getattr(g, "color", None)])

    bucket_counts = _bucket_categories(garments)
    gap_analysis = _build_gap_analysis(garments)
    readiness = _occasion_readiness(garments)
    usage = _usage_metrics(garments, outfits)
    sustainability = calculate_outfit_sustainability_score(garments)

    ideal_mix = {"tops": 0.32, "bottoms": 0.24, "footwear": 0.18, "accessories": 0.16, "outerwear": 0.10}
    wardrobe_balance_penalty = 0.0
    for key, target_share in ideal_mix.items():
        current_share = bucket_counts.get(key, 0) / total_items
        wardrobe_balance_penalty += abs(current_share - target_share) * 100
    wardrobe_balance = _clamp(100 - wardrobe_balance_penalty)

    seasons_present = sum(1 for season in ["spring", "summer", "fall", "winter"] if season_counts.get(season, 0) > 0)
    seasonal_coverage = _clamp((seasons_present / 4) * 100)

    readiness_scores = [item["score"] for item in readiness] or [0.0]
    versatility = _clamp((sum(readiness_scores) / len(readiness_scores)) * 0.55 + usage.get("usage_coverage", 0.0) * 0.45)

    insights = []
    dominant_style = style_counts.most_common(1)[0][0] if style_counts else "mixed"
    insights.append(f"Dominant style signature: {dominant_style}.")
    insights.append(f"Wardrobe balance score is {wardrobe_balance}/100 with {usage.get('usage_coverage', 0.0)}% item utilization.")
    if gap_analysis:
        worst_gap = gap_analysis[0]
        insights.append(f"Primary gap: {worst_gap['area']} coverage is below target.")
    else:
        insights.append("No critical wardrobe gaps detected across core categories.")

    return {
        "total_items": total_items,
        "category_distribution": [{"name": k, "count": v, "share": _pct(v, total_items)} for k, v in category_counts.most_common()],
        "style_distribution": [{"name": k, "count": v, "share": _pct(v, total_items)} for k, v in style_counts.most_common()],
        "season_distribution": [{"name": k, "count": v, "share": _pct(v, total_items)} for k, v in season_counts.most_common()],
        "palette": [{"color": k, "count": v, "share": _pct(v, total_items)} for k, v in color_counts.most_common(8)],
        "bucket_counts": bucket_counts,
        "readiness": readiness,
        "gaps": gap_analysis,
        "usage": usage,
        "scores": {
            "wardrobe_balance": wardrobe_balance,
            "seasonal_coverage": seasonal_coverage,
            "versatility": versatility,
            "sustainability": float(sustainability.get("score", 0)),
        },
        "sustainability": sustainability,
        "insights": insights,
    }


def explain_recommendation(
    outfit: List[Garment],
    all_garments: List[Garment],
    occasion: str,
    city: Optional[str] = None,
    user_preferences: Optional[Dict] = None,
    history_profile: Optional[Dict] = None,
) -> Dict:
    outfit = outfit or []
    all_garments = all_garments or []
    user_preferences = user_preferences or {}
    history_profile = history_profile or {}

    if not outfit:
        return {
            "summary": [],
            "item_breakdown": [],
            "metrics": {
                "harmony_score": 0.0,
                "completeness_score": 0.0,
                "preference_alignment": 0.0,
                "sustainability_score": 0.0,
            },
            "context": {
                "occasion": normalize_occasion(occasion),
                "city": city,
                "history_applied": bool(history_profile.get("has_learning")),
            },
        }

    normalized_occasion = normalize_occasion(occasion)
    base_item = outfit[0]
    item_breakdown = []
    pair_scores = []
    preference_hits = 0

    preferred_styles = {str(s).lower() for s in (user_preferences.get("preferred_styles") or [])}
    preferred_colors = {str(c).lower() for c in (user_preferences.get("preferred_colors") or [])}
    preferred_brands = {str(b).lower() for b in (user_preferences.get("preferred_brands") or [])}

    for index, garment in enumerate(outfit):
        reasons = []
        harmony = 1.0 if index == 0 else get_color_harmony_score(base_item.color, garment.color)
        if index > 0:
            pair_scores.append(harmony)
            if harmony >= 0.9:
                reasons.append("Strong color harmony with the anchor garment.")
            elif harmony >= 0.8:
                reasons.append("Good color compatibility for a balanced outfit.")

        if (garment.style or "").lower() in preferred_styles:
            preference_hits += 1
            reasons.append("Matches stored style preferences.")
        if (garment.color or "").lower() in preferred_colors:
            preference_hits += 1
            reasons.append("Matches preferred color palette.")
        if getattr(garment, "brand", None) and garment.brand.lower() in preferred_brands:
            preference_hits += 1
            reasons.append("Uses a preferred brand.")
        if history_profile.get("has_learning"):
            learned_score = score_candidate(
                base_item.color,
                garment,
                user_preferences=user_preferences,
                target_season=(garment.season or None),
                history_profile=history_profile,
                occasion=normalized_occasion,
            )
            if learned_score >= 0.9:
                reasons.append("Ranks highly using learned outfit history.")

        item_breakdown.append({
            "id": garment.id,
            "filename": garment.filename,
            "category": garment.category,
            "style": garment.style,
            "season": garment.season,
            "fabric": getattr(garment, "fabric", None),
            "color": garment.color,
            "harmony_score": round(harmony * 100, 1),
            "reasons": reasons or ["Selected to complete the outfit structure."],
        })

    template_requirements = OCCASION_TEMPLATES.get(normalized_occasion, {"shirt", "pants", "shoes"})
    outfit_categories = {_normalize_category(getattr(g, "category", None)) for g in outfit}
    completeness = _pct(len(template_requirements.intersection(outfit_categories)), len(template_requirements))
    harmony_score = round(((sum(pair_scores) / len(pair_scores)) if pair_scores else 1.0) * 100, 1)
    preference_alignment = _clamp((preference_hits / max(1, len(outfit) * 2)) * 100)
    sustainability = calculate_outfit_sustainability_score(outfit)

    summary = [
        f"Built for {normalized_occasion} with {completeness}% template coverage.",
        f"Average color harmony is {harmony_score}%, indicating {'strong' if harmony_score >= 85 else 'moderate'} visual cohesion.",
    ]
    if history_profile.get("has_learning"):
        summary.append("Personal history influenced the ranking based on previous outfit ratings and recency.")
    elif user_preferences:
        summary.append("Preferences influenced ranking even without enough history for learning.")
    else:
        summary.append("Recommendation is based on wardrobe composition, occasion rules, and color science.")

    return {
        "summary": summary,
        "item_breakdown": item_breakdown,
        "metrics": {
            "harmony_score": harmony_score,
            "completeness_score": completeness,
            "preference_alignment": preference_alignment,
            "sustainability_score": float(sustainability.get("score", 0)),
        },
        "context": {
            "occasion": normalized_occasion,
            "city": city,
            "history_applied": bool(history_profile.get("has_learning")),
        },
    }
