"""
Advanced recommendation engine with detailed explanations and AI insights
"""

def generate_outfit_explanation(outfit_items, occasion, user_preferences=None, weather=None):
    """Generate detailed AI explanation for why an outfit was recommended"""
    
    if not outfit_items:
        return {"summary": ["No items to explain"], "details": {}}
    
    # Categorize items
    tops = [item for item in outfit_items if item.get('category', '').lower() in ['shirt', 'cardigan', 'jacket', 'blazer', 'trench_coat', 'kurta', 'blouse']]
    bottoms = [item for item in outfit_items if item.get('category', '').lower() in ['pants', 'shorts', 'skirt']]
    outerwear = [item for item in outfit_items if item.get('category', '').lower() in ['jacket', 'blazer', 'trench_coat', 'coat', 'cardigan']]
    
    explanation = {
        "summary": [],
        "occasion_fit": "",
        "color_theory": "",
        "style_reasoning": "",
        "fabric_suitability": "",
        "personal_style": "",
        "styling_tips": []
    }
    
    # Occasion-specific explanation
    occasion_explanations = {
        "casual": "This casual outfit balances comfort with style for relaxed settings.",
        "formal": "This formal ensemble ensures a polished and sophisticated appearance.",
        "professional": "This professional look combines authority with approachability for work.",
        "party": "This outfit strikes the perfect balance between bold and wearable for celebrations.",
        "weekend": "This comfortable yet stylish look is perfect for weekend activities.",
        "interview": "This outfit projects confidence and professionalism for your interview.",
        "travel": "This outfit prioritizes comfort and practicality for travel.",
        "date": "This outfit combines charm and confidence for a memorable date."
    }
    
    explanation["occasion_fit"] = occasion_explanations.get(occasion, "Perfect for your occasion.")
    
    # Color theory explanation
    if outfit_items:
        colors = [item.get('color', 'neutral').lower() for item in outfit_items]
        unique_colors = list(set(colors))
        
        if len(unique_colors) == 1:
            explanation["color_theory"] = f"Monochromatic palette in {unique_colors[0]} creates a sophisticated, cohesive look."
        elif len(unique_colors) == 2:
            explanation["color_theory"] = f"Two-tone combination of {unique_colors[0]} and {unique_colors[1]} provides visual interest while maintaining harmony."
        else:
            explanation["color_theory"] = f"Multi-color palette with {', '.join(unique_colors)} is expertly coordinated for maximum impact."
    
    # Style reasoning
    if outfit_items:
        styles = [item.get('style', 'casual').lower() for item in outfit_items]
        if all(s in ['casual', 'relaxed'] for s in styles):
            explanation["style_reasoning"] = "All pieces follow a cohesive casual aesthetic, creating a relaxed yet put-together vibe."
        elif all(s in ['formal', 'elegant'] for s in styles):
            explanation["style_reasoning"] = "Each piece maintains formal elegance, ensuring a consistently sophisticated presentation."
        else:
            explanation["style_reasoning"] = "This outfit mixes styles strategically to create visual depth and personality."
    
    # Fabric suitability
    if outfit_items:
        fabrics = [item.get('fabric', 'cotton').lower() for item in outfit_items]
        fabric_explanation = []
        
        if any('cotton' in f for f in fabrics):
            fabric_explanation.append("Cotton base ensures breathability and comfort")
        if any('silk' in f for f in fabrics):
            fabric_explanation.append("silk adds elegance and drape")
        if any('wool' in f for f in fabrics):
            fabric_explanation.append("wool provides structure and warmth")
        if any('blend' in f for f in fabrics):
            fabric_explanation.append("fabric blends offer durability and easy care")
        
        if fabric_explanation:
            explanation["fabric_suitability"] = f"Fabric selection: {', '.join(fabric_explanation)}."
    
    # Weather consideration
    if weather:
        weather_tips = []
        if weather.get('condition') == 'rainy':
            weather_tips.append("Layer with water-resistant outerwear")
        elif weather.get('condition') == 'sunny':
            weather_tips.append("Light fabrics help you stay cool")
        elif weather.get('temp', 20) < 15:
            weather_tips.append("Add warm layers for temperature")
        explanation["styling_tips"].extend(weather_tips)
    
    # Personal style tip
    explanation["personal_style"] = "This outfit reflects your personal style preferences and past outfit successes."
    
    # Generate summary
    summary_parts = [
        explanation["occasion_fit"],
        explanation["color_theory"],
        explanation["style_reasoning"]
    ]
    explanation["summary"] = [p for p in summary_parts if p]
    
    return explanation


def generate_style_profile(garment_history, user_data=None):
    """Generate comprehensive personal style profile with personality type"""
    
    if not garment_history:
        return {"style_type": "Discovering", "personality": "Building your style identity"}
    
    # Count styles
    style_counts = {}
    color_counts = {}
    occasion_counts = {}
    
    for item in garment_history:
        style = item.get('style', 'casual').lower()
        color = item.get('color', 'neutral').lower()
        
        style_counts[style] = style_counts.get(style, 0) + 1
        color_counts[color] = color_counts.get(color, 0) + 1
    
    # Also add from outfit history if available
    if user_data and user_data.get('outfit_history'):
        for outfit in user_data['outfit_history']:
            occasion = outfit.get('occasion', 'casual').lower()
            occasion_counts[occasion] = occasion_counts.get(occasion, 0) + 1
    
    # Determine dominant style
    dominant_style = max(style_counts, key=style_counts.get) if style_counts else 'casual'
    
    # Style personality types
    style_types = {
        'casual': {
            'name': 'Casual Chic',
            'personality': 'Approachable and down-to-earth, you value comfort without sacrificing style',
            'characteristics': ['Comfortable', 'Relaxed', 'Practical', 'Approachable'],
            'colors': ['Neutrals', 'Earth tones', 'Soft pastels']
        },
        'formal': {
            'name': 'Elegant Professional',
            'personality': 'Sophisticated and refined, you make a statement with polished style',
            'characteristics': ['Elegant', 'Sophisticated', 'Professional', 'Refined'],
            'colors': ['Classic blacks', 'Deep jewel tones', 'Neutrals']
        },
        'trendy': {
            'name': 'Fashion Forward',
            'personality': 'Bold and creative, you love exploring new styles and pushing boundaries',
            'characteristics': ['Bold', 'Creative', 'Adventurous', 'Trendsetting'],
            'colors': ['Vibrant', 'Unconventional', 'Statement colors']
        },
        'bohemian': {
            'name': 'Bohemian Spirit',
            'personality': 'Free-spirited and artistic, your style reflects your unique personality',
            'characteristics': ['Artistic', 'Free-spirited', 'Individualistic', 'Expressive'],
            'colors': ['Warm earth tones', 'Jewel tones', 'Saturated colors']
        },
        'minimal': {
            'name': 'Minimalist',
            'personality': 'Clean and intentional, less is more in your fashion philosophy',
            'characteristics': ['Minimalist', 'Intentional', 'Quality-focused', 'Understated'],
            'colors': ['Neutrals', 'Monochrome', 'Grayscale']
        },
        'elegant': {
            'name': 'Classic Elegance',
            'personality': 'Timeless and refined, you appreciate quality and classic beauty',
            'characteristics': ['Classic', 'Timeless', 'Refined', 'Quality-conscious'],
            'colors': ['Neutral palette', 'Classic combinations', 'Timeless']
        }
    }
    
    style_profile = style_types.get(dominant_style, {
        'name': 'Eclectic Mix',
        'personality': 'You have a unique approach to fashion, blending various styles',
        'characteristics': ['Eclectic', 'Versatile', 'Individualistic', 'Expressive'],
        'colors': ['Diverse palette', 'Varied combinations', 'Personal preference']
    })
    
    # Top colors
    top_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Top occasions
    top_occasions = sorted(occasion_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    profile = {
        "style_type": style_profile.get('name', 'Discovering'),
        "personality": style_profile.get('personality', 'Building your style identity'),
        "characteristics": style_profile.get('characteristics', []),
        "color_palette": [c[0] for c in top_colors],
        "occasion_readiness": {occ[0]: round(occ[1] / len(garment_history) * 100) if garment_history else 0 for occ in top_occasions},
        "style_strengths": [],
        "style_recommendations": [],
        "versatility_score": calculate_versatility_score(garment_history)
    }
    
    # Add style strengths
    if 'trendy' in style_counts:
        profile["style_strengths"].append("You stay on top of fashion trends")
    if color_counts:
        unique_colors = len(color_counts)
        if unique_colors > 5:
            profile["style_strengths"].append("You're comfortable mixing diverse colors")
        else:
            profile["style_strengths"].append("You have a curated color palette")
    
    # Add recommendations
    if dominant_style == 'casual':
        profile["style_recommendations"].append("Try adding one statement piece for visual interest")
        profile["style_recommendations"].append("Experiment with layering for depth")
    elif dominant_style == 'formal':
        profile["style_recommendations"].append("Consider adding casual pieces for everyday wear")
        profile["style_recommendations"].append("Mix in accessories for personality")
    
    return profile


def calculate_versatility_score(garment_history):
    """Calculate how versatile a wardrobe is (0-100 scale)"""
    
    if not garment_history:
        return 0
    
    # Factors: variety of styles, colors, and occasions they can be worn for
    styles = len(set(item.get('style', '') for item in garment_history))
    colors = len(set(item.get('color', '') for item in garment_history))
    categories = len(set(item.get('category', '') for item in garment_history))
    
    # Normalize to 0-100
    style_score = min(len(garment_history), styles) / max(len(garment_history), styles or 1) * 30
    color_score = min(colors, 10) / 10 * 30
    category_score = min(categories, 8) / 8 * 40
    
    return min(100, int(style_score + color_score + category_score))


def generate_styling_tips(outfit_items, occasion, body_type=None, user_preferences=None):
    """Generate specific styling tips for an outfit"""
    
    tips = []
    
    # Occasion-specific tips
    occasion_tips = {
        "casual": [
            "Layer with a light cardigan for dimension",
            "Add sneakers or flats for comfort",
            "Use accessories to elevate casual basics"
        ],
        "formal": [
            "Ensure crisp, wrinkle-free fabric presentation",
            "Add classic jewelry for sophistication",
            "Keep accessories minimal and elegant"
        ],
        "interviews": [
            "Choose neutral colors to maintain focus on your words",
            "Avoid distracting patterns or large jewelry",
            "Ensure outfit is comfortable so you can focus"
        ],
        "date": [
            "Choose colors that complement your complexion",
            "Add a touch of personality with accessories",
            "Ensure comfort so you can focus on enjoying yourself"
        ],
        "party": [
            "Add statement jewelry or a bold accessory",
            "Consider shoes that make a statement",
            "Layer for visual interest and versatility"
        ]
    }
    
    tips.extend(occasion_tips.get(occasion, []))
    
    # Body type specific tips
    if body_type:
        body_type_tips = {
            "apple": ["Wear structured fabrics", "Avoid tight waistbands", "Draw attention upward with necklaces"],
            "pear": ["Wear wider or darker tops", "Brighten bottoms with lighter shades", "Use horizontal stripes on top"],
            "hourglass": ["Wear fitted styles", "Emphasize your natural curves", "Use wrap dresses"],
            "rectangle": ["Use ruffles and layers", "Create dimension with patterns", "Add curves with peplum tops"],
            "inverted_triangle": ["Draw attention downward", "Wear pattern on bottoms", "Use wide-leg pants"]
        }
        tips.extend(body_type_tips.get(body_type.lower(), []))
    
    return list(set(tips))  # Remove duplicates
