"""
Shopping assistance and recommendations for complementary items.
"""
from urllib.parse import quote_plus
import colorsys
from typing import List, Dict

SHOPPING_PARTNERS = [
    {"name": "Myntra", "url": "https://www.myntra.com/{query_slug}", "weight": 1.0},
    {"name": "Ajio", "url": "https://www.ajio.com/search/?text={query}", "weight": 0.96},
    {"name": "Flipkart", "url": "https://www.flipkart.com/search?q={query}", "weight": 0.93},
    {"name": "H&M", "url": "https://www2.hm.com/en_in/search-results.html?q={query}", "weight": 0.94},
    {"name": "Amazon Fashion", "url": "https://www.amazon.in/s?k={query}", "weight": 0.95},
]

BASE_TO_TARGET_CATEGORY_AFFINITY = {
    "shirt": {"pants": 1.0, "skirt": 0.93, "bag": 0.82, "watch": 0.8, "earrings": 0.84, "belt": 0.76},
    "pants": {"shirt": 1.0, "blazer": 0.91, "jacket": 0.88, "bag": 0.8, "watch": 0.78, "necklace": 0.72, "belt": 0.85},
    "shorts": {"shirt": 0.95, "shorts": 1.0, "blazer": 0.88, "jacket": 0.85, "bag": 0.82, "watch": 0.78, "belt": 0.83},
    "skirt": {"shirt": 1.0, "blazer": 0.9, "bag": 0.82, "watch": 0.76, "necklace": 0.8},
    "dress": {"shoes": 1.0, "bag": 0.96, "earrings": 0.94, "bracelet": 0.86, "necklace": 0.89},
    "watch": {"shirt": 0.82, "pants": 0.8, "dress": 0.76, "bag": 0.78, "bracelet": 0.65},
    "bag": {"shirt": 0.86, "pants": 0.82, "dress": 0.88, "watch": 0.79, "earrings": 0.8},
    "earrings": {"dress": 0.92, "shirt": 0.84, "bag": 0.8, "bracelet": 0.78},
}

CATEGORY_KEYWORDS = {
    "shirt": ["shirt", "blouse", "top", "t-shirt", "dress shirt"],
    "pants": ["pants", "jeans", "trousers", "leggings", "shorts"],
    "shorts": ["shorts", "short pants", "hot pants", "athletic shorts", "bermuda shorts", "denim shorts", "cargo shorts"],
    "dress": ["dress", "gown", "maxi dress", "mini dress"],
    "shoes": ["shoes", "sneakers", "heels", "boots", "sandals"],
    "cardigan": ["cardigan", "sweater", "pullover", "hoodie"],
    "coat": ["coat", "jacket", "blazer", "trench coat"],
    "accessories": ["necklace", "bracelet", "ring", "earrings", "watch"],
}

ACCESSORY_CATEGORIES = {
    "necklace", "bracelet", "earrings", "watch", "hat", "gloves", "scarf", "belt", "bag"
}

ESSENTIAL_ACCESSORIES = {
    "women": ["bag", "watch", "earrings", "bracelet", "necklace", "belt", "scarf"],
    "men": ["watch", "belt", "bag", "hat", "scarf"],
    "unisex": ["watch", "bag", "belt", "scarf", "hat"],
}


def normalize_category(garment_category: str) -> str:
    category = (garment_category or "").strip().lower()
    synonyms = {
        "top": "shirt",
        "tshirt": "shirt",
        "t-shirt": "shirt",
        "tee": "shirt",
        "blouse": "shirt",
        "trouser": "pants",
        "trousers": "pants",
        "jeans": "pants",
        "denim": "pants",
        "bottom": "pants",
        "sneaker": "shoes",
        "heel": "shoes",
        "loafer": "shoes",
    }
    return synonyms.get(category, category)


def normalize_gender(gender: str) -> str:
    token = (gender or "").strip().lower()
    if token in {"female", "woman", "women", "girl", "lady"}:
        return "women"
    if token in {"male", "man", "men", "boy", "gent"}:
        return "men"
    return "unisex"


def infer_gender_from_context(default_gender: str, text: str, category: str) -> str:
    if default_gender != "unisex":
        return default_gender

    token = f"{text or ''} {category or ''}".lower()
    women_markers = ["dress", "kurti", "kurta", "blouse", "skirt", "women", "lady", "female"]
    men_markers = ["mens", "men", "male", "chinos", "formal shirt men", "cargo men"]

    if any(m in token for m in women_markers):
        return "women"
    if any(m in token for m in men_markers):
        return "men"
    return "unisex"


def infer_subtype_from_text(text: str, fallback: str = "") -> str:
    token = (text or "").lower()
    rules = [
        ("wide leg", "wide_leg"),
        ("wideleg", "wide_leg"),
        ("flare", "flare"),
        ("cargo", "cargo"),
        ("jean", "jeans"),
        ("denim", "jeans"),
        ("trouser", "trousers"),
        ("chino", "chinos"),
        ("formal", "formal"),
        ("skirt", "skirt"),
        ("short", "shorts"),
        ("tee", "tshirt"),
        ("t-shirt", "tshirt"),
        ("shirt", "shirt"),
        ("blazer", "blazer"),
        ("kurti", "kurti"),
        ("kurta", "kurta"),
    ]
    for needle, label in rules:
        if needle in token:
            return label
    return fallback or "generic"


def hex_to_rgb(hex_color: str):
    hex_color = (hex_color or "").lstrip("#")
    if len(hex_color) != 6:
        return (128, 128, 128)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def hue_to_color_name(hue: float) -> str:
    buckets = [
        (0.04, "red"),
        (0.10, "orange"),
        (0.16, "yellow"),
        (0.33, "green"),
        (0.52, "blue"),
        (0.72, "purple"),
        (0.86, "pink"),
        (1.00, "red"),
    ]
    for upper, name in buckets:
        if hue <= upper:
            return name
    return "black"


def get_target_color_keywords(base_hex: str) -> List[str]:
    r, g, b = hex_to_rgb(base_hex)
    h, s, _ = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    if s < 0.2:
        return ["black", "white", "beige", "navy", "grey"]

    complementary_h = (h + 0.5) % 1.0
    analogous_1 = (h + 0.08) % 1.0
    analogous_2 = (h - 0.08) % 1.0
    triadic_h = (h + 0.33) % 1.0
    candidates = [
        hue_to_color_name(analogous_1),
        hue_to_color_name(complementary_h),
        hue_to_color_name(triadic_h),
        hue_to_color_name(analogous_2),
        "black",
        "white",
    ]

    dedup = []
    seen = set()
    for c in candidates:
        if c not in seen:
            dedup.append(c)
            seen.add(c)
    return dedup


def build_store_url(template: str, query: str) -> str:
    encoded = quote_plus(query)
    slug = query.strip().lower().replace(" ", "-")
    return template.format(query=encoded, query_slug=slug)


def get_query_blueprint(normalized_category: str, normalized_gender: str, style: str, fabric: str, subtype: str) -> Dict[str, List[str]]:
    style = (style or "").lower()
    fabric = (fabric or "").lower()

    if normalized_category in {"shirt", "cardigan", "jacket", "blazer", "trench_coat"}:
        if style == "formal" or normalized_category == "blazer":
            bottoms = ["tailored trousers", "straight fit pants", "ankle trousers"]
        elif subtype in {"tshirt", "shirt"} and fabric in {"denim", "cotton"}:
            bottoms = ["straight jeans", "chinos", "wide leg pants"]
        elif subtype in {"kurti", "kurta"}:
            bottoms = ["leggings", "palazzo pants", "straight pants"]
        else:
            bottoms = ["wide leg pants", "straight pants", "high waist pants"]

        return {
            "match_type": "matching_bottoms_for_top",
            "primary_categories": ["pants", "skirt"] if normalized_gender == "women" else ["pants", "shorts"],
            "accessory_categories": ["bag", "watch", "belt"] if normalized_gender != "women" else ["bag", "watch", "earrings"],
            "category_terms": {
                "pants": bottoms,
                "shorts": ["tailored shorts", "casual shorts"],
                "skirt": ["midi skirt", "pleated skirt", "straight skirt"],
                "bag": ["structured handbag", "crossbody bag", "sling bag"],
                "watch": ["minimal watch", "classic wrist watch"],
                "belt": ["leather belt", "formal belt"],
                "earrings": ["minimal earrings", "stud earrings"],
            },
            "compatibility_note": "Bottom type suggestions are generated based on selected top style and subtype."
        }

    if normalized_category in {"pants", "shorts", "skirt"}:
        if subtype in {"jeans", "cargo"}:
            tops = ["fitted top", "casual shirt", "graphic t-shirt"]
        elif subtype in {"trousers", "formal"}:
            tops = ["blouse", "formal shirt", "structured blazer"]
        elif subtype in {"wide_leg", "flare"}:
            tops = ["fitted top", "bodysuit top", "short shirt"]
        elif subtype == "skirt":
            tops = ["blouse", "fitted top", "cropped shirt"]
        else:
            tops = ["shirt", "top", "blouse"]

        # For shorts, also include similar shorts in recommendations
        if normalized_category == "shorts":
            if style == "formal" or subtype == "formal":
                shorts_terms = ["tailored shorts", "chino shorts", "smart casual shorts"]
                tops = ["formal shirt", "polo shirt", "linen shirt"] if normalized_gender != "women" else ["blouse", "structured top", "linen shirt"]
            elif subtype in {"jeans", "cargo"}:
                shorts_terms = ["denim shorts", "cargo shorts", "casual shorts"]
                tops = ["graphic t-shirt", "casual shirt", "fitted top"] if normalized_gender == "women" else ["t-shirt", "casual shirt", "polo shirt"]
            elif fabric == "cotton":
                shorts_terms = ["cotton shorts", "casual shorts", "bermuda shorts"]
                tops = ["casual shirt", "fitted top", "oversized t-shirt"] if normalized_gender == "women" else ["casual shirt", "polo shirt", "linen shirt"]
            else:
                shorts_terms = ["casual shorts", "bermuda shorts", "relaxed fit shorts"]
                tops = ["casual shirt", "top", "blouse"] if normalized_gender == "women" else ["casual shirt", "polo shirt", "t-shirt"]

            return {
                "match_type": "similar_and_matching_for_bottom",
                "primary_categories": ["shirt", "shorts"] if normalized_gender == "women" else ["shirt", "shorts"],
                "accessory_categories": ["belt", "watch", "bag"] if normalized_gender != "women" else ["bag", "watch", "necklace"],
                "category_terms": {
                    "shorts": shorts_terms,
                    "shirt": tops,
                    "bag": ["tote bag", "crossbody bag", "mini bag"],
                    "watch": ["classic watch", "minimal wrist watch"],
                    "belt": ["casual belt", "leather belt"],
                    "necklace": ["minimal necklace", "layered necklace"],
                },
                "compatibility_note": "Showing similar shorts styles plus matching tops for your current shorts."
            }

        return {
            "match_type": "matching_tops_for_bottom",
            "primary_categories": ["shirt", "blazer"] if normalized_gender == "women" else ["shirt", "jacket"],
            "accessory_categories": ["belt", "watch", "bag"] if normalized_gender != "women" else ["bag", "watch", "necklace"],
            "category_terms": {
                "shirt": tops,
                "blazer": ["blazer", "structured jacket"],
                "jacket": ["light jacket", "bomber jacket"],
                "bag": ["tote bag", "crossbody bag", "mini bag"],
                "watch": ["classic watch", "minimal wrist watch"],
                "belt": ["casual belt", "leather belt"],
                "necklace": ["minimal necklace", "layered necklace"],
            },
            "compatibility_note": "Top suggestions are tuned to your bottom type (jeans/trousers/wide leg/etc.)."
        }

    if normalized_category in ACCESSORY_CATEGORIES:
        return {
            "match_type": "accessory_anchor",
            "primary_categories": ["shirt", "pants", "dress"] if normalized_gender == "women" else ["shirt", "pants", "jacket"],
            "accessory_categories": [c for c in ESSENTIAL_ACCESSORIES.get(normalized_gender, ESSENTIAL_ACCESSORIES["unisex"]) if c != normalized_category],
            "category_terms": {
                "shirt": ["solid shirt", "classic shirt", "minimal top"],
                "pants": ["straight pants", "tailored trousers", "dark denim"],
                "dress": ["solid dress", "midi dress", "casual dress"],
                "jacket": ["light jacket", "casual blazer"],
                "bag": ["crossbody bag", "structured bag", "everyday bag"],
                "watch": ["classic watch", "minimal wrist watch"],
                "belt": ["clean leather belt", "formal belt"],
                "earrings": ["small earrings", "stud earrings"],
                "bracelet": ["minimal bracelet", "chain bracelet"],
                "necklace": ["simple necklace", "layered necklace"],
                "scarf": ["light scarf", "printed scarf"],
                "hat": ["baseball cap", "bucket hat"],
                "gloves": ["winter gloves", "knit gloves"],
            },
            "compatibility_note": "Accessory-first mode: suggestions include clothing anchors plus complementary accessories."
        }

    return {
        "match_type": "no_top_bottom_match_for_category",
        "primary_categories": [],
        "accessory_categories": ESSENTIAL_ACCESSORIES.get(normalized_gender, ESSENTIAL_ACCESSORIES["unisex"])[:3],
        "category_terms": {},
        "compatibility_note": "Fallback mode: showing versatile accessory suggestions for this category."
    }


def _build_search_query(gender: str, color: str, intent: str, style: str, fabric: str) -> str:
    color_token = (color or "").lower()
    style_token = (style or "").lower()
    fabric_token = (fabric or "").lower()

    tokens = [gender]
    if color_token not in {"black", "white", "grey"}:
        tokens.append(color_token)
    tokens.append(intent)
    if style_token and style_token not in intent.lower():
        tokens.append(style_token)
    if fabric_token and fabric_token not in intent.lower() and fabric_token not in {"synthetic"}:
        tokens.append(fabric_token)
    return " ".join([t for t in tokens if t and t != "unisex"])


def _category_rank_multiplier(category: str) -> float:
    priority = {
        "shirt": 1.0,
        "pants": 1.0,
        "shorts": 1.0,
        "skirt": 0.98,
        "dress": 0.98,
        "jacket": 0.96,
        "blazer": 0.96,
        "bag": 0.95,
        "watch": 0.95,
        "belt": 0.94,
        "earrings": 0.93,
        "bracelet": 0.92,
        "necklace": 0.92,
        "scarf": 0.9,
        "hat": 0.88,
        "gloves": 0.86,
    }
    return priority.get(category, 0.84)


def _style_match_multiplier(style: str, intent: str) -> float:
    token_style = (style or "").lower()
    token_intent = (intent or "").lower()
    if not token_style:
        return 0.92
    if token_style in token_intent:
        return 1.0
    if token_style == "formal" and any(k in token_intent for k in ["tailored", "structured", "classic", "minimal"]):
        return 0.97
    if token_style == "casual" and any(k in token_intent for k in ["casual", "everyday", "denim", "graphic"]):
        return 0.97
    return 0.9


def _fabric_match_multiplier(fabric: str, intent: str) -> float:
    token_fabric = (fabric or "").lower()
    token_intent = (intent or "").lower()
    if not token_fabric:
        return 0.93
    if token_fabric in token_intent:
        return 1.0
    if token_fabric in {"cotton", "denim", "linen"}:
        return 0.95
    return 0.9


def _category_affinity_multiplier(base_category: str, target_category: str) -> float:
    base_key = normalize_category(base_category)
    target_key = normalize_category(target_category)
    affinity_map = BASE_TO_TARGET_CATEGORY_AFFINITY.get(base_key, {})
    return affinity_map.get(target_key, 0.74 if target_key in ACCESSORY_CATEGORIES else 0.8)


def _intent_specificity_multiplier(intent: str, subtype: str, style: str) -> float:
    token_intent = (intent or "").lower()
    token_subtype = (subtype or "").lower()
    token_style = (style or "").lower()
    score = 0.9
    if token_subtype and token_subtype != "generic" and token_subtype.replace("_", " ") in token_intent:
        score += 0.08
    if token_style and token_style in token_intent:
        score += 0.05
    if any(term in token_intent for term in ["tailored", "structured", "minimal", "classic", "straight", "wide leg"]):
        score += 0.03
    return min(score, 1.02)


def _curate_top_links(links: List[dict], primary_categories: List[str], accessory_categories: List[str]) -> List[dict]:
    primary_limit = 6
    accessory_limit = 6
    curated = []
    used_pairs = set()

    def add_from_pool(pool: List[dict], limit: int):
        count = 0
        for link in pool:
            if count >= limit:
                break
            pair_key = (link["store"], link["category"])
            if pair_key in used_pairs:
                continue
            curated.append(link)
            used_pairs.add(pair_key)
            count += 1

    primary_pool = [link for link in links if link["category"] in primary_categories]
    accessory_pool = [link for link in links if link["category"] in accessory_categories]
    fallback_pool = [link for link in links if link not in primary_pool and link not in accessory_pool]

    for category in primary_categories:
        category_pool = [link for link in primary_pool if link["category"] == category]
        add_from_pool(category_pool, 3)

    add_from_pool(primary_pool, primary_limit)
    add_from_pool(accessory_pool, accessory_limit)
    add_from_pool(fallback_pool, 4)

    return curated[:12]


def _normalize_confidence_score(raw_score: float) -> float:
    # Absolute clamp for safety; relative normalization is applied after ranking.
    return round(max(0.0, min(raw_score, 2.0)), 4)


def _spread_confidence_scores(links: List[dict]) -> List[dict]:
    if not links:
        return links

    raw_scores = [float(link.get("raw_confidence", link.get("confidence", 0.0)) or 0.0) for link in links]
    min_score = min(raw_scores)
    max_score = max(raw_scores)
    spread = max_score - min_score

    for link in links:
        raw = float(link.get("raw_confidence", link.get("confidence", 0.0)) or 0.0)
        if spread < 0.02:
            normalized = 0.82
        else:
            relative = (raw - min_score) / spread
            normalized = 0.55 + (relative * 0.4)
        link["confidence"] = round(min(0.95, max(0.55, normalized)), 3)
    return links


def get_complementary_items(
    garment_category: str,
    garment_color: str,
    gender: str = None,
    style: str = None,
    fabric: str = None,
    filename: str = None,
    description: str = None
) -> dict:
    """Get shopping recommendations for complementary items."""
    normalized_category = normalize_category(garment_category)
    normalized_gender = normalize_gender(gender)

    subtype_text = " ".join([
        str(filename or ""),
        str(description or ""),
        str(garment_category or ""),
        str(style or ""),
        str(fabric or ""),
    ])
    inferred_subtype = infer_subtype_from_text(subtype_text)
    normalized_gender = infer_gender_from_context(normalized_gender, subtype_text, garment_category)

    color_keywords = get_target_color_keywords(garment_color)
    blueprint = get_query_blueprint(
        normalized_category=normalized_category,
        normalized_gender=normalized_gender,
        style=style or "",
        fabric=fabric or "",
        subtype=inferred_subtype,
    )

    primary_categories = blueprint.get("primary_categories", [])
    accessory_categories = blueprint.get("accessory_categories", [])
    categories_to_shop = primary_categories + accessory_categories
    category_terms = blueprint["category_terms"]
    match_type = blueprint["match_type"]

    recommendations = {
        "category": garment_category,
        "normalized_category": normalized_category,
        "inferred_subtype": inferred_subtype,
        "gender": normalized_gender,
        "color": garment_color,
        "target_colors": color_keywords,
        "match_type": match_type,
        "online_strategy": {
            "primary_categories": primary_categories,
            "accessory_categories": accessory_categories,
        },
        "compatibility_note": blueprint.get("compatibility_note", ""),
        "shopping_plan": {
            "core_focus": primary_categories[:2],
            "accessory_focus": accessory_categories[:2],
            "capsule_note": blueprint.get("compatibility_note", ""),
        },
        "complementary_items": {},
        "shopping_links": []
    }

    seen_links = set()
    used_store_category = set()
    for category in categories_to_shop:
        keywords = CATEGORY_KEYWORDS.get(category, [category])
        intent_terms = category_terms.get(category, [keywords[0]])
        is_accessory = category in ACCESSORY_CATEGORIES

        recommendations["complementary_items"][category] = {
            "description": f"Shop {normalized_gender} {category} matching your {normalized_category}",
            "keywords": keywords,
            "query_terms": intent_terms,
            "price_range": get_price_range_for_category(category),
            "type": "accessory" if is_accessory else "core"
        }

        for store_idx, store in enumerate(SHOPPING_PARTNERS):
            for intent_idx, intent in enumerate(intent_terms[:3]):
                chosen_color = color_keywords[(store_idx + intent_idx) % len(color_keywords)]
                query = _build_search_query(normalized_gender, chosen_color, intent, style or "", fabric or "")
                url = build_store_url(store["url"], query)

                key = (store["name"], category, url)
                if key in seen_links:
                    continue
                seen_links.add(key)

                style_fit = _style_match_multiplier(style or "", intent)
                fabric_fit = _fabric_match_multiplier(fabric or "", intent)
                category_fit = _category_rank_multiplier(category)
                affinity_fit = _category_affinity_multiplier(normalized_category, category)
                specificity_fit = _intent_specificity_multiplier(intent, inferred_subtype, style or "")
                novelty_penalty = 0.93 if (store["name"], category) in used_store_category else 1.0
                used_store_category.add((store["name"], category))
                intent_decay = 1 - (intent_idx * 0.10)
                accessory_bonus = 1.02 if is_accessory else 1.05

                ranking_score = round(
                    (store["weight"] * 0.28)
                    + (intent_decay * 0.14)
                    + (style_fit * 0.13)
                    + (fabric_fit * 0.08)
                    + (category_fit * 0.1)
                    + (affinity_fit * 0.18)
                    + (specificity_fit * 0.09),
                    3
                )
                ranking_score = round(ranking_score * novelty_penalty * accessory_bonus, 3)
                ranking_score = _normalize_confidence_score(ranking_score)
                recommendations["shopping_links"].append({
                    "store": store["name"],
                    "category": category,
                    "query": query,
                    "target_color": chosen_color,
                    "intent": intent,
                    "is_accessory": is_accessory,
                    "priority": "accessory" if is_accessory else "core",
                    "confidence": ranking_score,
                    "raw_confidence": ranking_score,
                    "url": url
                })

    recommendations["shopping_links"].sort(key=lambda l: l.get("confidence", 0), reverse=True)
    recommendations["shopping_links"] = _spread_confidence_scores(recommendations["shopping_links"])
    recommendations["shopping_links"].sort(key=lambda l: l.get("confidence", 0), reverse=True)
    recommendations["shopping_links"] = _curate_top_links(
        recommendations["shopping_links"],
        primary_categories=primary_categories,
        accessory_categories=accessory_categories,
    )
    return recommendations


def get_price_range_for_category(category: str) -> dict:
    price_ranges = {
        "shirt": {"min": 20, "max": 100, "currency": "USD"},
        "pants": {"min": 40, "max": 150, "currency": "USD"},
        "dress": {"min": 50, "max": 200, "currency": "USD"},
        "shoes": {"min": 50, "max": 200, "currency": "USD"},
        "cardigan": {"min": 50, "max": 150, "currency": "USD"},
        "coat": {"min": 100, "max": 400, "currency": "USD"},
        "accessories": {"min": 15, "max": 100, "currency": "USD"},
    }
    return price_ranges.get(category, {"min": 30, "max": 150, "currency": "USD"})


def find_trend_items(category: str, current_color: str) -> list:
    trending_items = {
        "shirt": [
            {"name": "Oversized Linen Shirt", "trend": "2024", "colors": ["white", "beige", "light blue"]},
            {"name": "Crop Top", "trend": "ongoing", "colors": ["black", "white", "pastels"]},
            {"name": "Silk Blouse", "trend": "classic", "colors": ["white", "black", "jewel tones"]},
        ],
        "pants": [
            {"name": "Wide-Leg Trousers", "trend": "2024", "colors": ["black", "brown", "grey"]},
            {"name": "High-Waisted Jeans", "trend": "ongoing", "colors": ["dark blue", "black", "light wash"]},
            {"name": "Cargo Pants", "trend": "rising", "colors": ["khaki", "black", "olive"]},
        ],
        "shoes": [
            {"name": "White Sneakers", "trend": "classic", "colors": ["white"]},
            {"name": "Ballet Flats", "trend": "2024", "colors": ["black", "nude", "metallic"]},
            {"name": "Chunky Loafers", "trend": "rising", "colors": ["black", "brown", "burgundy"]},
        ],
    }
    return trending_items.get(category, [])


def get_sustainability_tips(category: str) -> dict:
    sustainability_info = {
        "shirt": {
            "sustainable_materials": ["organic cotton", "linen", "hemp", "bamboo"],
            "care_tips": "Wash in cold water, air dry when possible",
            "lifespan": "3-5 years with proper care",
            "eco_brands": ["Patagonia", "Everlane", "Reformation"]
        },
        "pants": {
            "sustainable_materials": ["organic cotton", "recycled polyester", "linen"],
            "care_tips": "Minimize washing, spot clean when possible",
            "lifespan": "4-7 years",
            "eco_brands": ["Patagonia", "Nudie Jeans", "Rag & Bone"]
        },
        "shoes": {
            "sustainable_materials": ["recycled materials", "plant-based leather", "organic cotton"],
            "care_tips": "Rotate shoes to extend lifespan",
            "lifespan": "2-3 years",
            "eco_brands": ["Allbirds", "Veja", "Rothy's"]
        },
    }

    return sustainability_info.get(category, {
        "sustainable_materials": ["natural fibers", "recycled materials"],
        "care_tips": "Follow garment care labels",
        "lifespan": "2-5 years",
        "eco_brands": ["Search for certified sustainable brands"]
    })


def calculate_outfit_sustainability_score(garments: list) -> dict:
    score = 80
    tips = []

    if len(garments) < 2:
        tips.append("Add more pieces to your wardrobe for mix-and-match options")

    return {
        "score": score,
        "level": "good",
        "tips": tips,
        "environmental_impact": {
            "water_usage": "medium",
            "carbon_footprint": "low-medium",
            "waste_reduction": "high"
        }
    }
