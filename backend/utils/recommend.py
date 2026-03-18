# backend/utils/recommend.py
from typing import List, Dict
from models import Garment
from services.weather import get_weather
import colorsys
import random

ACCESSORY_CATEGORIES = {
    "necklace", "bracelet", "earrings", "watch", "hat", "gloves", "scarf", "belt", "bag"
}

TOP_CATEGORIES = {"shirt", "cardigan", "jacket", "blazer", "trench_coat", "kurta"}
BOTTOM_CATEGORIES = {"pants", "shorts", "skirt"}
FOOTWEAR_CATEGORIES = {"shoes", "boots", "sandals"}


def hex_to_rgb(hex_color: str):
    """Convert hex (#RRGGBB) to RGB tuple."""
    hex_color = (hex_color or "").lstrip('#')
    if len(hex_color) != 6:
        return (128, 128, 128)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hsv(rgb: tuple) -> tuple:
    """Convert RGB to HSV for color harmony calculations."""
    r, g, b = [x / 255.0 for x in rgb]
    return colorsys.rgb_to_hsv(r, g, b)


def is_color_harmony(base_color: str, candidate_color: str) -> bool:
    """Check if two colors have good harmony based on hue distance and saturation."""
    try:
        base_rgb = hex_to_rgb(base_color)
        cand_rgb = hex_to_rgb(candidate_color)

        base_saturation = colorsys.rgb_to_hsv(base_rgb[0] / 255, base_rgb[1] / 255, base_rgb[2] / 255)[1]
        cand_saturation = colorsys.rgb_to_hsv(cand_rgb[0] / 255, cand_rgb[1] / 255, cand_rgb[2] / 255)[1]

        if base_saturation < 0.15 or cand_saturation < 0.15:
            return True

        base_hsv = rgb_to_hsv(base_rgb)
        cand_hsv = rgb_to_hsv(cand_rgb)

        hue_diff = abs(base_hsv[0] - cand_hsv[0])
        hue_diff = min(hue_diff, 1 - hue_diff)
        return (hue_diff < 0.15 or (0.25 < hue_diff < 0.4) or (0.4 < hue_diff < 0.6))
    except Exception:
        return True


def get_color_harmony_score(base_color: str, candidate_color: str) -> float:
    """Get a numeric score (0-1) for how well two colors work together."""
    try:
        base_rgb = hex_to_rgb(base_color)
        cand_rgb = hex_to_rgb(candidate_color)

        base_h, base_s, _ = rgb_to_hsv(base_rgb)
        cand_h, cand_s, _ = rgb_to_hsv(cand_rgb)

        if base_s < 0.15 or cand_s < 0.15:
            return 0.95

        hue_diff = abs(base_h - cand_h)
        hue_diff = min(hue_diff, 1 - hue_diff)

        if hue_diff < 0.08:
            score = 0.85
        elif 0.08 <= hue_diff < 0.15:
            score = 0.90
        elif 0.25 <= hue_diff < 0.35:
            score = 0.88
        elif 0.4 <= hue_diff < 0.6:
            score = 0.92
        else:
            score = 0.70

        sat_diff = abs(base_s - cand_s)
        if sat_diff < 0.2:
            score += 0.05
        elif sat_diff > 0.4:
            score -= 0.1

        return min(score, 1.0)
    except Exception:
        return 0.5


def normalize_occasion(occasion: str) -> str:
    """Normalize specific events to base recommendation templates."""
    occasion = (occasion or "casual").lower().strip()
    aliases = {
        "office": "professional",
        "meeting": "professional",
        "wedding": "party",
        "trip": "weekend",
    }
    return aliases.get(occasion, occasion)


def _score_history_signal(history_profile: Dict, key: str, value: str) -> float:
    if not history_profile or not value:
        return 0.0
    liked = history_profile.get(f"liked_{key}", {}) or {}
    disliked = history_profile.get(f"disliked_{key}", {}) or {}
    v = str(value).lower()
    return (liked.get(v, 0.0) * 0.08) - (disliked.get(v, 0.0) * 0.09)


def score_candidate(
    base_color: str,
    garment: Garment,
    user_preferences: Dict = None,
    target_season: str = None,
    history_profile: Dict = None,
    occasion: str = None,
    temperature: float = None,
    weather_condition: str = None,
) -> float:
    """Rank a candidate using color harmony, preferences, seasonal fit, temperature, and learning signals."""
    score = get_color_harmony_score(base_color, garment.color)
    user_preferences = user_preferences or {}
    history_profile = history_profile or {}

    preferred_styles = {str(s).lower() for s in (user_preferences.get("preferred_styles") or [])}
    preferred_colors = {str(c).lower() for c in (user_preferences.get("preferred_colors") or [])}
    preferred_brands = {str(b).lower() for b in (user_preferences.get("preferred_brands") or [])}

    g_style = (garment.style or "").lower()
    g_color = (garment.color or "").lower()
    g_category = (garment.category or "").lower()

    if preferred_styles and g_style in preferred_styles:
        score += 0.1
    if preferred_colors and g_color in preferred_colors:
        score += 0.12
    if preferred_brands and getattr(garment, "brand", None):
        if garment.brand.lower() in preferred_brands:
            score += 0.08
    if target_season and garment.season == target_season:
        score += 0.07

    # TEMPERATURE-BASED SCORING (NEW) - Heavy weighting for weather-appropriate items
    if temperature is not None:
        if temperature <= 0:
            # Freezing - strongly prefer heavy layers
            if g_category in {"trench_coat", "jacket", "sweater", "cardigan"}:
                score += 0.25
            if (garment.fabric or "").lower() in {"wool", "fleece", "down"}:
                score += 0.15
        elif temperature < 5:
            # Very cold
            if g_category in {"trench_coat", "jacket", "sweater", "cardigan"}:
                score += 0.2
            if (garment.fabric or "").lower() in {"wool", "fleece", "down"}:
                score += 0.12
        elif temperature < 10:
            # Cold
            if g_category in {"cardigan", "sweater", "jacket"}:
                score += 0.15
        elif temperature < 15:
            # Cool
            if g_category in {"cardigan", "sweater"}:
                score += 0.1
        elif temperature > 30:
            # Hot - strongly prefer light layers
            if g_category in {"shirt", "kurta", "dress", "shorts"}:
                score += 0.2
            if (garment.fabric or "").lower() in {"cotton", "linen", "silk"}:
                score += 0.15
            # Penalize heavy items in hot weather
            if g_category in {"trench_coat", "jacket", "sweater", "cardigan"}:
                score -= 0.15
        elif temperature > 25:
            # Warm
            if g_category in {"shirt", "kurta", "dress"}:
                score += 0.12
            if g_category in {"shorts"}:
                score += 0.08
            # Light penalty for heavy items
            if g_category in {"trench_coat", "sweater"}:
                score -= 0.08
        elif temperature > 20:
            # Moderate-Warm
            if g_category in {"shirt", "kurta"}:
                score += 0.08
    
    # WEATHER CONDITION-BASED SCORING (NEW)
    if weather_condition:
        weather_lower = weather_condition.lower()
        if "rain" in weather_lower:
            if g_category in {"trench_coat", "jacket"}:
                score += 0.15
            if (garment.fabric or "").lower() in {"polyester", "nylon", "waterproof"}:
                score += 0.1
        elif "sunny" in weather_lower or "clear" in weather_lower:
            if g_category in {"dress", "shorts", "shirt", "kurta"}:
                score += 0.1
        elif "humid" in weather_lower:
            if (garment.fabric or "").lower() in {"cotton", "linen"}:
                score += 0.1
            # Breathable fabrics more important
            if (garment.fabric or "").lower() not in {"cotton", "linen", "silk"}:
                score -= 0.05

    # Learned taste from outfit history
    score += _score_history_signal(history_profile, "styles", g_style)
    score += _score_history_signal(history_profile, "colors", g_color)
    score += _score_history_signal(history_profile, "categories", g_category)

    garment_affinity = (history_profile.get("garment_affinity") or {}).get(str(getattr(garment, "id", "")), 0.0)
    score += garment_affinity * 0.08

    occ = normalize_occasion(occasion or "")
    occ_style_bias = (history_profile.get("occasion_style_bias") or {}).get(occ, {})
    if g_style in occ_style_bias:
        score += max(-0.12, min(0.12, occ_style_bias[g_style] * 0.06))

    return score


def recommend_outfit(
    occasion: str,
    garments: List[Garment],
    city: str = None,
    user_preferences: Dict = None,
    history_profile: Dict = None,
) -> List[Garment]:
    """Recommend a complete outfit based on occasion, weather, preferences, and learned history."""
    if not garments:
        return []

    occasion = normalize_occasion(occasion)
    history_profile = history_profile or {}

    available = {}
    for g in garments:
        category = (g.category or "").lower()
        if category not in available:
            available[category] = []
        available[category].append(g)

    occasion_templates = {
        "casual": [["shirt"], ["pants"], ["shoes", "boots", "sandals"], ["accessory"]],
        "formal": [["dress"], ["shoes", "boots", "sandals"], ["accessory"]],
        "professional": [["shirt"], ["pants"], ["shoes", "boots", "sandals"], ["accessory"]],
        "party": [["dress"], ["shoes", "boots", "sandals"], ["accessory"]],
        "weekend": [["shirt"], ["pants"], ["shoes", "boots", "sandals"], ["cardigan", "jacket"], ["accessory"]],
        "travel": [["shirt"], ["pants"], ["shoes", "boots", "sandals"], ["jacket", "cardigan", "trench_coat"], ["accessory"]],
        "interview": [["shirt"], ["pants"], ["blazer", "jacket"], ["shoes", "boots", "sandals"], ["accessory"]],
        "date": [["dress"], ["shoes", "boots", "sandals"], ["accessory"]],
    }

    fallback_templates = {
        "formal": [["shirt"], ["pants", "skirt"], ["shoes", "boots", "sandals"], ["accessory"]],
        "party": [["shirt"], ["skirt", "pants"], ["shoes", "boots", "sandals"], ["accessory"]],
        "date": [["shirt"], ["skirt", "pants"], ["shoes", "boots", "sandals"], ["accessory"]],
    }

    template_slots = occasion_templates.get(occasion, [["shirt"], ["pants"], ["shoes", "boots", "sandals"]])

    target_season = None
    temp = None  # Initialize for use in fallback fill_slots calls
    weather = None  # Initialize for use in fallback fill_slots calls
    
    if city:
        try:
            weather_data = get_weather(city)
            weather = weather_data.get("condition", "Unknown").lower()
            temp = weather_data.get("temp", 25)
            humidity = weather_data.get("humidity", 60)

            # RAIN handling - highest priority
            if "rain" in weather:
                template_slots = [["shirt"], ["pants"], ["shoes", "boots"], ["accessory"]]
                if "trench_coat" in available:
                    template_slots.insert(2, ["trench_coat"])
                elif any(cat in available for cat in ["jacket", "cardigan"]):
                    for cat in ["jacket", "cardigan"]:
                        if cat in available:
                            template_slots.insert(2, [cat])
                            break
            # VERY HOT (>30°C) - remove heavy layers
            elif temp > 30:
                template_slots = [
                    slot for slot in template_slots
                    if not any(option in {"trench_coat", "cardigan", "jacket", "blazer", "sweater"} for option in slot)
                ]
                # Ensure shorts/light clothing
                if any(any(opt in available for opt in ["shorts"]) for _ in [1]):
                    template_slots = [["shirt", "kurta"], ["shorts"], ["sandals", "shoes"], ["accessory"]]
            # HOT (20-30°C) - light clothing
            elif temp > 20:
                # Remove heavy outer layers but keep some options
                template_slots = [
                    slot for slot in template_slots
                    if not any(option in {"trench_coat", "sweater"} for option in slot)
                ]
                # Add shorts option
                for slot in template_slots:
                    if "pants" in slot and "shorts" in available:
                        slot.append("shorts")
            # COOL (10-20°C) - add light layers
            elif 10 <= temp <= 20:
                if "cardigan" in available:
                    template_slots.append(["cardigan"])
                if "sweater" in available:
                    template_slots.append(["sweater"])
                if "jacket" in available:
                    template_slots.append(["jacket"])
            # COLD (<10°C) - add warm layers
            elif temp < 10:
                if "cardigan" in available:
                    template_slots.append(["cardigan"])
                if "sweater" in available:
                    template_slots.append(["sweater"])
                if "jacket" in available:
                    template_slots.append(["jacket"])
            # VERY COLD (<5°C) - heavy outerwear
            if temp < 5:
                if "trench_coat" in available:
                    template_slots.insert(2, ["trench_coat"])
                elif "jacket" in available:
                    template_slots.insert(2, ["jacket"])
                if "sweater" in available:
                    template_slots.insert(2, ["sweater"])

            # Humidity consideration for fabric type
            if humidity > 70:
                # Prefer breathable fabrics - prioritize shirt/kurta over heavy materials
                for i, slot in enumerate(template_slots):
                    if "shirt" in slot or "kurta" in slot:
                        break
            
            # Set target season based on temperature range
            if temp >= 28:
                target_season = "summer"
            elif temp <= 12:
                target_season = "winter"
            elif temp < 5:
                target_season = "winter"
            else:
                target_season = "spring"
        except Exception as e:
            # If weather API fails, still try to improve recommendations
            pass

    selected_items = []
    selected_ids = set()

    def pick_best_from_categories(category_options, temp=None, weather=None):
        pool = []
        for option in category_options:
            if option == "accessory":
                continue
            pool.extend([g for g in available.get(option, []) if g.id not in selected_ids])
        if not pool:
            return None

        if selected_items:
            base_color = selected_items[0].color
            return max(
                pool,
                key=lambda g: score_candidate(
                    base_color,
                    g,
                    user_preferences,
                    target_season,
                    history_profile=history_profile,
                    occasion=occasion,
                    temperature=temp,
                    weather_condition=weather,
                ),
            )

        def first_item_score(g):
            base = 0.5
            base += _score_history_signal(history_profile, "styles", (g.style or "").lower())
            base += _score_history_signal(history_profile, "colors", (g.color or "").lower())
            base += _score_history_signal(history_profile, "categories", (g.category or "").lower())
            if user_preferences and (g.style or "").lower() in {str(s).lower() for s in (user_preferences.get("preferred_styles") or [])}:
                base += 0.08
            # Temperature scoring for first item
            if temp is not None:
                g_category = (g.category or "").lower()
                if temp > 30 and g_category in {"shirt", "kurta", "dress", "shorts"}:
                    base += 0.15
                elif temp < 10 and g_category in {"cardigan", "sweater", "jacket"}:
                    base += 0.15
            return base

        return max(pool, key=first_item_score)

    def fill_slots(slots, temp=None, weather=None):
        for slot in slots:
            if "accessory" in slot:
                continue
            chosen = pick_best_from_categories(slot, temp=temp, weather=weather)
            if not chosen:
                continue
            selected_items.append(chosen)
            selected_ids.add(chosen.id)

    fill_slots(template_slots, temp=temp if city else None, weather=weather if city else None)

    # Occasion-aware fallback if the primary template is unavailable.
    if len(selected_items) < 2 and occasion in fallback_templates:
        fill_slots(fallback_templates[occasion], temp=temp if city else None, weather=weather if city else None)

    # Safety fallback: always prefer one top + one bottom + one footwear before arbitrary items.
    if len(selected_items) < 2:
        fallback_roles = [list(TOP_CATEGORIES), list(BOTTOM_CATEGORIES), list(FOOTWEAR_CATEGORIES)]
        fill_slots(fallback_roles, temp=temp if city else None, weather=weather if city else None)

    # Final fallback: only if wardrobe is extremely sparse.
    if not selected_items:
        return garments[: min(3, len(garments))]

    for category_options in template_slots:
        if "accessory" not in category_options:
            continue
        break

    desired_accessory_count = 2 if occasion in {"party", "date", "formal"} else 1
    accessory_candidates = [
        g for g in garments
        if (g.category or "").lower() in ACCESSORY_CATEGORIES and g.id not in selected_ids
    ]
    if accessory_candidates and selected_items:
        anchor_color = selected_items[0].color
        ranked_accessories = sorted(
            accessory_candidates,
            key=lambda g: score_candidate(
                anchor_color,
                g,
                user_preferences,
                target_season,
                history_profile=history_profile,
                occasion=occasion,
            ),
            reverse=True,
        )
        used_accessory_categories = set()
        for g in ranked_accessories:
            cat = (g.category or "").lower()
            if cat in used_accessory_categories:
                continue
            selected_items.append(g)
            selected_ids.add(g.id)
            used_accessory_categories.add(cat)
            if len(used_accessory_categories) >= desired_accessory_count:
                break

    return selected_items if selected_items else garments[:3]


def get_what_to_wear_today(
    garments: List[Garment],
    city: str = None,
    user_preferences: Dict = None,
    history_profile: Dict = None,
) -> List[Garment]:
    """Suggest what to wear today based on weather, preferences, and learned behavior."""
    return recommend_outfit("casual", garments, city, user_preferences, history_profile)


def find_color_combinations(base_color: str, garments: List[Garment]) -> Dict:
    """Find garments that work well with a specific color."""
    combinations = {
        "complementary": [],
        "analogous": [],
        "neutral": []
    }

    base_h = rgb_to_hsv(hex_to_rgb(base_color))[0]
    for g in garments:
        hue_diff = abs(base_h - rgb_to_hsv(hex_to_rgb(g.color))[0])
        hue_diff = min(hue_diff, 1 - hue_diff)

        if 0.4 < hue_diff < 0.6:
            combinations["complementary"].append(g)
        elif hue_diff < 0.1:
            combinations["analogous"].append(g)
        else:
            combinations["neutral"].append(g)

    return combinations


def get_suitable_matches(base_garment: Garment, garments: List[Garment], outfit_type: str = "complete") -> List[Garment]:
    """Recommend suitable garments to pair with a selected base garment."""
    complements = {
        "shirt": ["pants", "shorts", "skirt", "shoes", "boots", "sandals", "watch", "belt", "bag", "necklace"],
        "cardigan": ["pants", "shorts", "skirt", "shoes", "boots", "watch", "bag", "scarf"],
        "jacket": ["pants", "shorts", "skirt", "shoes", "boots", "watch", "bag", "scarf"],
        "blazer": ["pants", "skirt", "shoes", "boots", "watch", "belt", "bag"],
        "trench_coat": ["pants", "skirt", "shoes", "boots", "bag", "scarf"],
        "pants": ["shirt", "cardigan", "jacket", "blazer", "shoes", "boots", "sandals", "belt", "watch", "bag"],
        "shorts": ["shirt", "cardigan", "jacket", "shoes", "sandals", "watch", "bag", "hat"],
        "skirt": ["shirt", "cardigan", "jacket", "blazer", "shoes", "boots", "sandals", "belt", "bag", "necklace"],
        "dress": ["cardigan", "jacket", "shoes", "boots", "sandals", "necklace", "bracelet", "earrings", "watch", "bag"],
        "kurta": ["cardigan", "jacket", "pants", "shoes", "sandals", "earrings", "bracelet", "bag", "scarf"],
        "necklace": ["dress", "shirt", "kurta", "earrings", "bracelet", "bag"],
        "bracelet": ["dress", "shirt", "kurta", "watch", "bag"],
        "earrings": ["dress", "shirt", "kurta", "necklace", "bag"],
        "watch": ["shirt", "blazer", "pants", "dress", "bag", "shoes"],
        "hat": ["shirt", "shorts", "dress", "sandals", "bag"],
        "gloves": ["jacket", "trench_coat", "boots", "scarf", "bag"],
        "scarf": ["shirt", "dress", "jacket", "trench_coat", "boots", "bag"],
        "belt": ["pants", "skirt", "dress", "shirt", "shoes", "bag"],
        "bag": ["shirt", "pants", "dress", "skirt", "kurta", "shoes", "watch", "scarf"],
        "shoes": ["shirt", "pants", "dress", "skirt", "kurta", "bag", "watch"],
        "boots": ["jacket", "trench_coat", "pants", "dress", "bag", "scarf"],
        "sandals": ["dress", "skirt", "shorts", "kurta", "bag", "bracelet"],
    }

    role_priority = {
        "shirt": ["pants", "shorts", "skirt", "shoes", "boots", "sandals"],
        "cardigan": ["pants", "shorts", "skirt", "shoes", "boots"],
        "jacket": ["pants", "shorts", "skirt", "shoes", "boots"],
        "blazer": ["pants", "skirt", "shoes", "boots"],
        "trench_coat": ["pants", "skirt", "shoes", "boots"],
        "pants": ["shirt", "cardigan", "jacket", "blazer"],
        "shorts": ["shirt", "cardigan", "jacket"],
        "skirt": ["shirt", "cardigan", "jacket", "blazer"],
        "dress": ["cardigan", "jacket", "shoes", "boots", "sandals"],
        "kurta": ["pants", "shirt", "sandals"],
        "watch": ["shirt", "dress", "blazer"],
        "bag": ["shirt", "pants", "dress", "skirt"],
        "shoes": ["shirt", "pants", "dress", "skirt"],
        "boots": ["jacket", "pants", "dress"],
        "sandals": ["dress", "skirt", "shorts", "kurta"],
    }

    base_category = (base_garment.category or "").lower()
    complement_categories = complements.get(base_category, [])
    if not complement_categories:
        return [g for g in garments if g.id != base_garment.id and g.style == base_garment.style]

    prioritized_categories = role_priority.get(base_category, complement_categories)

    def candidate_pool(preferred_categories):
        return [
            g for g in garments
            if (g.category or "").lower() in preferred_categories
            and g.id != base_garment.id
            and g.style == base_garment.style
            and g.season == base_garment.season
        ]

    candidates = candidate_pool(prioritized_categories)
    if len(candidates) < 2:
        candidates = [
            g for g in garments
            if (g.category or "").lower() in prioritized_categories
            and g.id != base_garment.id
            and g.style == base_garment.style
        ]

    if len(candidates) < 2:
        candidates = [
            g for g in garments
            if (g.category or "").lower() in prioritized_categories
            and g.id != base_garment.id
        ]

    if len(candidates) < 2:
        candidates = [
        g for g in garments
            if (g.category or "").lower() in complement_categories
            and g.id != base_garment.id
        ]

    candidates.sort(
        key=lambda g: (
            (g.category or "").lower() in prioritized_categories,
            get_color_harmony_score(base_garment.color, g.color),
            g.style == base_garment.style,
            g.season == base_garment.season,
            getattr(g, "fabric", None) == getattr(base_garment, "fabric", None),
        ),
        reverse=True,
    )

    return candidates[:5]
