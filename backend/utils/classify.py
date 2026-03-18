import numpy as np
import os
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image as keras_image
from PIL import Image
import colorsys
from scipy import ndimage

mobilenet_model = MobileNetV2(weights='imagenet')

ACCESSORY_CATEGORIES = {
    "necklace", "bracelet", "earrings", "watch", "hat", "gloves", "scarf", "belt", "bag"
}

# ML Model to Category Mapping
# Maps ImageNet predictions to our clothing categories
ml_prediction_mapping = {
    # Pants/Bottoms
    'pants': 'pants',
    'trousers': 'pants',
    'jeans': 'pants',
    'khakis': 'pants',
    'sweatpants': 'pants',
    'pajama': 'pants',  # Pajama bottoms look like pants to model
    'shower_curtain': 'pants',  # Long hanging fabric can look like pants
    'wardrobe': 'pants',  # If it detects "wardrobe" it's likely pants hanging
    
    # Dresses/Skirts
    'dress': 'dress',
    'gown': 'dress',
    'evening_gown': 'dress',
    'miniskirt': 'skirt',
    'skirt': 'skirt',
    'sundress': 'dress',
    'maxi_skirt': 'skirt',
    
    # Tops/Shirts
    'shirt': 'shirt',
    't-shirt': 'shirt',
    'blouse': 'shirt',
    'tank_top': 'shirt',
    'polo_shirt': 'shirt',
    'sweatshirt': 'shirt',
    'hoodie': 'shirt',
    'sweater': 'cardigan',
    'cardigan': 'cardigan',
    
    # Footwear
    'shoe': 'shoes',
    'sneaker': 'shoes',
    'boot': 'boots',
    'sandal': 'sandals',
    'loafer': 'shoes',
    'high_heels': 'shoes',
    'flip-flop': 'sandals',
    
    # Outerwear
    'coat': 'trench_coat',
    'parka': 'trench_coat',
    'jacket': 'jacket',
    'blazer': 'blazer',
    'windbreaker': 'jacket',
    
    # Accessories
    'bag': 'bag',
    'purse': 'bag',
    'handbag': 'bag',
    'backpack': 'bag',
    'necklace': 'necklace',
    'bracelet': 'bracelet',
    'watch': 'watch',
    'analog_clock': 'watch',
    'digital_watch': 'watch',
    'stopwatch': 'watch',
    'scarf': 'scarf',
    'hat': 'hat',
}

# Enhanced categories with more detailed keywords
category_keywords = {
    'pants': ['jeans', 'jean', 'pant', 'pants', 'trousers', 'denim', 'cargo', 'chino', 'trouser'],
    'shorts': ['shorts', 'short pants'],
    'dress': ['dress', 'gown', 'frock', 'minidress', 'maxi', 'saree', 'evening dress'],
    'kurta': ['kurta', 'abaya', 'tunic', 'kurti', 'ethnic tunic', 'indian tunic'],
    'shirt': ['shirt', 'suit', 'tshirt', 'blouse', 'jersey', 'top', 'polo', 'button-up', 'casual shirt', 't-shirt'],
    'skirt': ['skirt', 'pleated', 'pencil skirt'],
    'shoes': ['shoe', 'sneaker', 'loafer', 'heel', 'sandal', 'slipper', 'oxford'],
    'boots': ['boot', 'ankle boot', 'knee-high'],
    'sandals': ['sandal', 'flip-flop', 'gladiator'],
    'cardigan': ['cardigan', 'sweater', 'pullover', 'jumper', 'knit', 'woolly'],
    'jacket': ['jacket', 'bomber', 'denim jacket', 'leather jacket'],
    'blazer': ['blazer', 'sport coat', 'formal jacket'],
    'trench_coat': ['coat', 'trench', 'overcoat', 'parka', 'peacoat'],
    'necklace': ['necklace', 'chain', 'pendant', 'amulet', 'choker'],
    'hat': ['hat', 'cap', 'beanie', 'beret'],
    'gloves': ['glove', 'mitten'],
    'scarf': ['scarf', 'shawl', 'wrap'],
    'bag': ['bag', 'purse', 'handbag', 'backpack', 'tote'],
    'bracelet': ['bracelet', 'bangle'],
    'earrings': ['earring'],
    'belt': ['belt', 'buckle'],
    'watch': ['watch', 'wristwatch']
}

def infer_accessory_from_filename(image_path: str) -> str:
    """Infer accessory category directly from filename tokens when explicit."""
    name = os.path.basename(image_path).lower()
    filename_hint_map = {
        "watch": "watch",
        "wristwatch": "watch",
        "necklace": "necklace",
        "bracelet": "bracelet",
        "earring": "earrings",
        "bag": "bag",
        "purse": "bag",
        "handbag": "bag",
        "backpack": "bag",
        "scarf": "scarf",
        "hat": "hat",
        "glove": "gloves",
        "belt": "belt",
    }
    for token, category in filename_hint_map.items():
        if token in name:
            return category
    return ""

def pick_accessory_override(decoded_predictions):
    """
    If ML strongly suggests an accessory, prefer it over visual misclassification.
    Returns mapped accessory category or empty string.
    """
    best_category = ""
    best_score = 0.0
    for _, label, prob in decoded_predictions:
        label_lower = label.lower()
        mapped = ml_prediction_mapping.get(label_lower, "")
        if not mapped:
            for category, keywords in category_keywords.items():
                if any(keyword in label_lower for keyword in keywords):
                    mapped = category
                    break
        if mapped in ACCESSORY_CATEGORIES and prob > best_score:
            best_category = mapped
            best_score = prob
    return best_category if best_score >= 0.12 else ""

def hex_to_rgb(hex_color: str):
    """Convert hex color to RGB."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_saturation_brightness(color: str):
    """Extract saturation and brightness from hex color."""
    try:
        rgb = hex_to_rgb(color)
        r, g, b = [x / 255.0 for x in rgb]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        return s, v
    except:
        return 0.5, 0.5

def analyze_garment_shape(image_path: str) -> dict:
    """
    Analyze garment shape and structure to determine category.
    Returns metrics about aspect ratio, width distribution, etc.
    """
    try:
        img = Image.open(image_path).convert('RGB')
        pixels = np.array(img)
        height_px, width_px = pixels.shape[0], pixels.shape[1]
        gray = np.mean(pixels, axis=2)
        
        print(f"[Shape Analysis] Image dimensions: {height_px}x{width_px}")
        print(f"[Shape Analysis] Gray value range: {np.min(gray):.1f} - {np.max(gray):.1f}")
        
        # Try multiple threshold strategies
        # Strategy 1: 40th percentile (darks)
        threshold1 = np.percentile(gray, 40)
        mask1 = gray < threshold1
        
        # Strategy 2: 50th percentile (darker half)
        threshold2 = np.percentile(gray, 50)
        mask2 = gray < threshold2
        
        # Strategy 3: Inverted - 70th percentile (for bright garments)
        threshold3 = np.percentile(gray, 70)
        mask3 = gray > threshold3
        
        fg1_count = np.sum(mask1)
        fg2_count = np.sum(mask2)
        fg3_count = np.sum(mask3)
        
        print(f"[Shape Analysis] Foreground pixels - thresh@40: {fg1_count}, thresh@50: {fg2_count}, thresh@70(inv): {fg3_count}")
        
        # Use the mask with reasonable foreground pixels (not too little, not too much)
        if fg1_count > 100 and fg1_count < height_px * width_px * 0.9:
            garment_mask = mask1
            print(f"[Shape Analysis] Using strategy 1 (40th percentile)")
        elif fg2_count > 100 and fg2_count < height_px * width_px * 0.9:
            garment_mask = mask2
            print(f"[Shape Analysis] Using strategy 2 (50th percentile)")
        elif fg3_count > 100 and fg3_count < height_px * width_px * 0.9:
            garment_mask = mask3
            print(f"[Shape Analysis] Using strategy 3 (70th percentile inverted)")
        else:
            print(f"[Shape Analysis] WARNING: No good threshold found!")
            # Try adaptive approach - use 30th percentile as last resort
            threshold_alt = np.percentile(gray, 30)
            garment_mask = gray < threshold_alt
            print(f"[Shape Analysis] Using fallback 30th percentile")
        
        if np.sum(garment_mask) < 100:  # Too few foreground pixels
            print(f"[Shape Analysis] ERROR: Still too few foreground pixels after fallback")
            return {}
        
        # Get vertical and horizontal profiles
        vertical_projection = np.sum(garment_mask, axis=1)
        horizontal_projection = np.sum(garment_mask, axis=0)
        
        # Find garment extent
        rows = np.where(vertical_projection > 0)[0]
        cols = np.where(horizontal_projection > 0)[0]
        
        if len(rows) == 0 or len(cols) == 0:
            print(f"[Shape Analysis] ERROR: No rows or columns detected in mask")
            return {}
        
        top, bottom = rows[0], rows[-1]
        left, right = cols[0], cols[-1]
        
        height = bottom - top
        width = right - left
        aspect_ratio = height / width if width > 0 else 0
        
        print(f"[Shape Analysis] Bounding box - Height: {height}, Width: {width}, Aspect Ratio: {aspect_ratio:.2f}")
        
        # Focus on main body (exclude flutter sleeves by looking at dense areas)
        density_per_row = np.sum(garment_mask[top:bottom, left:right], axis=1)
        mean_density = np.mean(density_per_row)
        dense_rows = np.where(density_per_row > mean_density * 0.5)[0]
        
        print(f"[Shape Analysis] Mean row density: {mean_density:.1f}, Dense rows: {len(dense_rows)}")
        
        if len(dense_rows) > 20:  # Only use dense row detection if we have enough
            main_top = top + dense_rows[0]
            main_bottom = top + dense_rows[-1]
            main_height = main_bottom - main_top
            print(f"[Shape Analysis] ✓ Main body detected: height {main_height}")
        else:
            main_height = height
            print(f"[Shape Analysis] ⚠ Using full height as main body (not enough dense rows: {len(dense_rows)})")
        
        # Top width vs bottom width (using main body)
        top_third_idx = max(1, (main_height // 3))
        top_third_width = np.sum(garment_mask[top:min(top+top_third_idx, bottom), left:right])
        bottom_third_width = np.sum(garment_mask[max(top, bottom-top_third_idx):bottom, left:right])
        
        width_ratio = bottom_third_width / (top_third_width + 0.001)
        print(f"[Shape Analysis] Width ratio (bottom/top): {width_ratio:.2f}")
        
        return {
            'aspect_ratio': aspect_ratio,
            'main_body_height': main_height,
            'width_ratio': width_ratio,
            'height': height,
            'width': width,
        }
    except Exception as e:
        print(f"[Shape Analysis] EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return {}

def classify_by_visual_features(image_path: str, shape_analysis: dict) -> tuple:
    """
    Classify garment using visual features and shape analysis.
    Returns (category, confidence).
    """
    try:
        if not shape_analysis:
            print("[Visual Analysis] Empty shape_analysis, returning default")
            return ('shirt', 0.5)
            
        edge_density, color_var, pattern_count = detect_embroidery_and_patterns(image_path)
        
        aspect_ratio = shape_analysis.get('aspect_ratio', 0)
        main_body_height = shape_analysis.get('main_body_height', 0)
        raw_height = shape_analysis.get('height', 0)
        width_ratio = shape_analysis.get('width_ratio', 1.0)
        
        # Decision tree based on visual features
        print(f"\n[Visual Analysis Decision Tree]")
        print(f"  Aspect Ratio: {aspect_ratio:.2f}, Width Ratio: {width_ratio:.2f}")
        print(f"  Main Body Height: {main_body_height}, Raw Height: {raw_height}")
        print(f"  Edge Density: {edge_density:.3f}, Color Variance: {color_var:.1f}, Patterns: {pattern_count}\n")
        
        # PRIORITY 1: SHORT items (main body < 250px) → SHIRT
        # This is the most reliable classifier
        if main_body_height < 250:
            print("[Visual Analysis] ✓ MATCHED: SHORT item (< 250px) → SHIRT")
            return ('shirt', 0.90)
        
        # PRIORITY 1.5: Moderate short (250-300px) with normal aspect → SHIRT
        if main_body_height < 300 and aspect_ratio < 1.5:
            print(f"[Visual Analysis] ✓ MATCHED: MODERATE SHORT (height {main_body_height}) → SHIRT")
            return ('shirt', 0.88)
        
        # PRIORITY 2: Very tall and narrow → PANTS (bottoms)
        # Key: Pants have HIGH aspect ratio (very tall relative to width)
        # Even wide-leg jeans maintain aspect_ratio > 1.7 because HEIGHT >> WIDTH
        # Dresses are more balanced (aspect_ratio 1.3-1.7)
        if aspect_ratio > 1.7:  # Aggressive threshold to catch all pants
            print(f"[Visual Analysis] ✓ MATCHED: VERY TALL (aspect {aspect_ratio:.1f}) → PANTS")
            return ('pants', 0.90)
        
        # PRIORITY 3: Tall with flared bottom (dress-like) → DRESS/KURTA
        # This catches dresses/skirts that flare out (width_ratio > 1.3)
        # But NOT pants which are tall but narrow (width_ratio < 1.3)
        if main_body_height > 300 and aspect_ratio > 1.3 and aspect_ratio < 1.7 and width_ratio > 1.3:
            print(f"[Visual Analysis] ✓ MATCHED: TALL & FLARED BOTTOM (h={main_body_height}, aspect {aspect_ratio:.1f}, ratio {width_ratio:.2f})")
            if edge_density > 0.15 or pattern_count > 60:
                print(f"            → KURTA (embroidery detected)")
                return ('kurta', 0.82)
            else:
                print(f"            → DRESS")
                return ('dress', 0.80)
        
        # PRIORITY 4: Long with embroidery → DRESS/KURTA
        if main_body_height > 300 and (edge_density > 0.15 or color_var > 60):
            print(f"[Visual Analysis] ✓ MATCHED: LONG WITH EMBROIDERY → DRESS/KURTA")
            if pattern_count > 60:
                return ('kurta', 0.82)
            else:
                return ('dress', 0.80)
        
        # Default based on aspect ratio
        if aspect_ratio > 1.5:
            print(f"[Visual Analysis] ✓ MATCHED: DEFAULT (tall) → PANTS (fallback)")
            return ('pants', 0.65)
        else:
            print(f"[Visual Analysis] ✓ MATCHED: DEFAULT (normal) → SHIRT (fallback)")
            return ('shirt', 0.70)
            
    except Exception as e:
        print(f"[Visual Analysis] Exception: {e}")
        import traceback
        traceback.print_exc()
        return ('shirt', 0.5)

def detect_embroidery_and_patterns(image_path: str) -> tuple:
    """Detect embroidery, buttons, and patterns in the image."""
    try:
        img = Image.open(image_path).convert('RGB')
        pixels = np.array(img)
        
        # Convert to grayscale for edge detection
        gray = np.mean(pixels, axis=2)
        
        # Detect edges using Sobel operator
        sx = ndimage.sobel(gray, axis=0)
        sy = ndimage.sobel(gray, axis=1)
        edges = np.sqrt(sx**2 + sy**2)
        
        # Calculate edge density (higher = more patterns/embroidery/buttons)
        edge_density = np.mean(edges > 50)  # Normalize by threshold
        
        # Detect color variations (embroidery often has bright accent colors)
        color_variance = np.std(pixels)
        
        # Check for structured patterns (buttons, grid patterns)
        # Use histogram to detect repeated intensities
        hist, _ = np.histogram(gray.flatten(), bins=256)
        peak_count = np.sum(hist > np.mean(hist) * 1.5)
        
        return edge_density, color_variance, peak_count
    except Exception as e:
        print(f"Error detecting patterns: {e}")
        return 0, 0, 0

def classify_garment(image_path):
    """Classify garment category using visual feature analysis (primary) + ML predictions (fallback)."""
    try:
        print(f"\n{'='*60}")
        print(f"[Classification] Starting classification for: {image_path}")
        print(f"{'='*60}")
        
        filename_hint = infer_accessory_from_filename(image_path)
        if filename_hint:
            print(f"[Classification] Filename accessory hint detected -> {filename_hint}")
            print(f"{'='*60}\n")
            return filename_hint

        # PRIMARY: Use visual feature analysis
        print("\n--- VISUAL FEATURE ANALYSIS ---")
        shape_analysis = analyze_garment_shape(image_path)
        
        print(f"\n[Classification] Shape analysis result: {shape_analysis}")
        
        visual_category, visual_confidence = ("", 0.0)
        if shape_analysis:
            visual_category, visual_confidence = classify_by_visual_features(image_path, shape_analysis)
            print(f"\n[Classification] Visual Analysis Result: {visual_category} (confidence: {visual_confidence})")
        else:
            print(f"\n[Classification] ⚠ shape_analysis is empty, skipping visual analysis")
        
        # ML model is always consulted so accessory predictions can correct visual mistakes.
        print("\n--- ML MODEL CHECK ---")
        img = keras_image.load_img(image_path, target_size=(224, 224))
        x = keras_image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        preds = mobilenet_model.predict(x, verbose=0)
        decoded = decode_predictions(preds, top=5)[0]
        
        print(f"[Classification Debug] ML Model Top 5 Predictions:")
        for idx, (_, label, prob) in enumerate(decoded):
            print(f"  {idx+1}. {label}: {prob:.4f}")

        accessory_override = pick_accessory_override(decoded)
        if accessory_override:
            print(f"[Classification] ✓ ACCESSORY OVERRIDE from ML -> {accessory_override}")
            print(f"{'='*60}\n")
            return accessory_override

        # If confidence is high (>0.75), use visual classification for clothing categories.
        if visual_confidence > 0.75:
            print(f"\n[Classification] ✓ HIGH CONFIDENCE - Using visual analysis: {visual_category}")
            print(f"{'='*60}\n")
            return visual_category
        elif visual_category:
            print(f"[Classification] ✗ LOW CONFIDENCE ({visual_confidence}) - Using ML fallback")
        
        best_match = None
        best_score = 0
        matches_by_category = {}
        
        for _, label, prob in decoded:
            label_lower = label.lower()
            
            # Try ML prediction mapping first
            if label_lower in ml_prediction_mapping:
                mapped_category = ml_prediction_mapping[label_lower]
                score = prob
                
                if mapped_category == 'pants':
                    score *= 1.3
                elif mapped_category in ['dress', 'kurta']:
                    score *= 1.2
                
                print(f"[Classification] ML '{label}' → '{mapped_category}' (score: {score:.4f})")
                
                if mapped_category not in matches_by_category or score > matches_by_category[mapped_category][1]:
                    matches_by_category[mapped_category] = (mapped_category, score)
                
                if score > best_score:
                    best_score = score
                    best_match = mapped_category
            else:
                # Fallback to keyword matching
                for category, keywords in category_keywords.items():
                    keyword_match = any(keyword in label_lower for keyword in keywords)
                    
                    if keyword_match:
                        score = prob
                        if category == 'pants':
                            score *= 1.2
                        
                        if category not in matches_by_category or score > matches_by_category[category][1]:
                            matches_by_category[category] = (category, score)
                        
                        if score > best_score:
                            best_score = score
                            best_match = category
        
        if best_match is None and matches_by_category:
            best_match = max(matches_by_category.items(), key=lambda x: x[1][1])[0]
        
        print(f"\n[Classification] ✓ Final Classification (ML Fallback): {best_match}")
        print(f"{'='*60}\n")
        return best_match if best_match else "shirt"
        
    except Exception as e:
        print(f"\n[Classification] ✗ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        return "shirt"

def detect_style(image_path: str, category: str = "") -> str:
    """Detect style (casual, formal, sport) based on image analysis and category hints."""
    try:
        # Category-based defaults for reliability
        category_lower = (category or "").lower()
        
        # Shorts, t-shirts, hoodies, athletic wear → casual
        if any(x in category_lower for x in ['shorts', 't-shirt', 'tee', 'hoodie', 'sweatshirt', 'athletic', 'sport', 'casual']):
            return "casual"
        
        # Blazers, formal shirts, dress pants, formal dresses → formal
        if any(x in category_lower for x in ['blazer', 'suit', 'tuxedo', 'tux', 'formal', 'gown', 'trousers']):
            return "formal"
        
        # Jackets, cardigans → usually casual but could be formal based on image
        # Skirts → could be either, needs image analysis
        # Fall through to image analysis for these
        
        img = Image.open(image_path)
        pixels = np.array(img)
        
        # Get pattern metrics
        edge_density, color_var, pattern_count = detect_embroidery_and_patterns(image_path)
        
        if len(pixels.shape) == 3:
            # Calculate color statistics
            r_mean, g_mean, b_mean = np.mean(pixels[:,:,0]), np.mean(pixels[:,:,1]), np.mean(pixels[:,:,2])
            r_std, g_std, b_std = np.std(pixels[:,:,0]), np.std(pixels[:,:,1]), np.std(pixels[:,:,2])
            
            color_variance = (r_std + g_std + b_std) / 3
            brightness = (r_mean + g_mean + b_mean) / 3
            saturation, val = get_saturation_brightness('#' + '%02x%02x%02x' % (int(r_mean), int(g_mean), int(b_mean)))
            
            # Formal indicators: highly structured patterns, embroidery, buttons (VERY CONSERVATIVE)
            # Much stricter thresholds to avoid false positives
            formal_score = edge_density * 100 + (color_var * 0.3)
            
            # Casual indicators: high color variance without strong structure
            casual_score = color_variance if color_variance > 85 else 0
            
            # Sport indicators: very bright, high contrast colors
            sport_score = brightness if brightness > 215 else 0
            
            # Decision logic with MUCH stricter thresholds
            # Formal requires BOTH high structured patterns AND high embroidery/button count
            if formal_score > 60 and edge_density > 0.3 and pattern_count > 150:
                return "formal"  # Strong structured patterns, embroidery, buttons
            elif casual_score > 0 and formal_score < 25:
                return "casual"  # High color variance, minimal structure
            elif sport_score > 0 and brightness > 220:
                return "sport"
            else:
                # Default: casual is safer than formal for ambiguous cases
                return "casual"
        
        return "casual"
    except Exception as e:
        print(f"Error detecting style: {e}")
        return "casual"

def detect_season(image_path: str, category: str = "") -> str:
    """Detect season based on clothing type and image analysis."""
    try:
        # Heuristics based on clothing category
        category = category.lower()
        
        # Heavy/warm clothing indicates winter or fall
        if any(x in category for x in ['coat', 'trench', 'cardigan', 'sweater', 'jacket', 'blazer', 'gloves', 'scarf']):
            if 'coat' in category or 'trench' in category:
                return "winter"
            return "fall"
        
        # Light clothing indicates spring or summer
        if any(x in category for x in ['dress', 'shorts', 'sandal', 'skirt']):
            return "summer"
        
        # Analyze image brightness
        img = Image.open(image_path)
        pixels = np.array(img)
        
        if len(pixels.shape) == 3:
            brightness = np.mean(pixels) / 255.0
            
            # Bright image = summer, darker = winter
            if brightness > 0.6:
                return "summer"
            elif brightness < 0.4:
                return "winter"
            else:
                # Mid-tone could be spring or fall
                return "spring"
        
        return "all"
    except Exception as e:
        print(f"Error detecting season: {e}")
        return "all"

def detect_fabric(image_path: str, category: str = "") -> str:
    """Heuristic fabric detection from filename keywords + texture statistics."""
    try:
        name = os.path.basename(image_path).lower()
        keyword_map = {
            "denim": "denim",
            "jean": "denim",
            "wool": "wool",
            "knit": "knit",
            "sweater": "knit",
            "silk": "silk",
            "satin": "silk",
            "linen": "linen",
            "leather": "leather",
            "suede": "leather",
            "cotton": "cotton",
        }
        for token, fabric in keyword_map.items():
            if token in name:
                return fabric

        edge_density, color_var, _ = detect_embroidery_and_patterns(image_path)
        category = (category or "").lower()

        # Handle accessories with appropriate materials
        ACCESSORY_CATEGORIES = {"watch", "necklace", "bracelet", "earrings", "ring", "bag", "belt", "hat", "gloves", "scarf"}
        if any(x in category for x in ACCESSORY_CATEGORIES):
            # For accessories, return material names instead of fabric terms
            if "watch" in category:
                return "metal"
            elif "leather" in name or "bag" in category or "belt" in category:
                return "leather"
            elif "gold" in name or "silver" in name or "rose" in name:
                return "metal"
            else:
                return "mixed"

        if "pants" in category and edge_density > 0.16:
            return "denim"
        if any(x in category for x in ["cardigan", "jacket", "coat", "trench"]):
            return "wool" if edge_density > 0.14 else "knit"
        if any(x in category for x in ["dress", "kurta", "shirt"]) and color_var < 38:
            return "linen"
        if edge_density < 0.08 and color_var < 35:
            return "silk"
        if edge_density > 0.2:
            return "synthetic"
        return "cotton"
    except Exception as e:
        print(f"Error detecting fabric: {e}")
        return "cotton"
