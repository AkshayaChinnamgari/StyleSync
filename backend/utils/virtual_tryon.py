"""
Virtual try-on and outfit preview generation utilities.
"""
from PIL import Image, ImageDraw, ImageFilter
import os
from typing import List
from models import Garment
import numpy as np
from collections import deque

UPLOAD_DIR = "static/uploads"
PREVIEW_DIR = "static/previews"
os.makedirs(PREVIEW_DIR, exist_ok=True)

TOP_CATEGORIES = {"shirt", "cardigan", "jacket", "blazer", "trench_coat"}
BOTTOM_CATEGORIES = {"pants", "shorts", "skirt"}
FULL_BODY_CATEGORIES = {"dress", "kurta"}
FOOTWEAR_CATEGORIES = {"shoes", "boots", "sandals"}
ACCESSORY_CATEGORIES = {"necklace", "bracelet", "earrings", "watch", "hat", "scarf", "belt", "bag"}

def category_group(category: str) -> str:
    c = (category or "").lower()
    if c in TOP_CATEGORIES:
        return "top"
    if c in BOTTOM_CATEGORIES:
        return "bottom"
    if c in FULL_BODY_CATEGORIES:
        return "full_body"
    if c in FOOTWEAR_CATEGORIES:
        return "footwear"
    if c in ACCESSORY_CATEGORIES:
        return "accessory"
    return "other"


def create_outfit_collage(garments: List[Garment], outfit_id: int) -> str:
    """
    Create a visual collage preview of selected outfit items.
    
    Args:
        garments: List of Garment objects
        outfit_id: ID for the outfit preview file
    
    Returns:
        str: Path to generated collage image
    """
    if not garments:
        return None
    
    # Create canvas
    cols = 3
    rows = (len(garments) + cols - 1) // cols
    item_width, item_height = 200, 250
    
    canvas_width = cols * item_width + 40
    canvas_height = rows * item_height + 40
    
    canvas = Image.new("RGB", (canvas_width, canvas_height), color="white")
    draw = ImageDraw.Draw(canvas)
    
    # Add items to canvas
    for idx, garment in enumerate(garments):
        row = idx // cols
        col = idx % cols
        
        x_start = 20 + col * item_width
        y_start = 20 + row * item_height
        
        try:
            # Load garment image
            img_path = os.path.join(UPLOAD_DIR, f"uploaded_{garment.filename}")
            if os.path.exists(img_path):
                item_img = Image.open(img_path).convert("RGBA")
                item_img.thumbnail((item_width - 10, item_height - 40), Image.Resampling.LANCZOS)
                
                # Paste onto canvas
                canvas.paste(item_img, (x_start + 5, y_start + 5), item_img)
        except Exception as e:
            print(f"Error loading image {garment.filename}: {e}")
        
        # Add label
        label = f"{garment.category}\n{garment.color}"
        draw.text((x_start + 5, y_start + item_height - 35), label, fill="black")
        
        # Draw border
        draw.rectangle([x_start, y_start, x_start + item_width, y_start + item_height], 
                      outline="gray", width=2)
    
    # Save collage
    output_path = os.path.join(PREVIEW_DIR, f"outfit_{outfit_id}.png")
    canvas.save(output_path)
    return output_path


def create_color_palette(garments: List[Garment]) -> str:
    """
    Create a color palette preview showing all colors in an outfit.
    
    Args:
        garments: List of Garment objects
    
    Returns:
        str: Path to color palette image
    """
    if not garments:
        return None
    
    # Create palette
    palette_width = 50 * len(garments)
    palette_height = 100
    
    palette = Image.new("RGB", (palette_width, palette_height), color="white")
    
    for idx, garment in enumerate(garments):
        x_start = idx * 50
        try:
            # Parse hex color
            color_hex = garment.color.lstrip('#')
            color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
            
            # Draw color block
            for y in range(palette_height):
                for x in range(x_start, x_start + 50):
                    if x < palette_width:
                        palette.putpixel((x, y), color_rgb)
        except:
            pass
    
    return palette


def enhance_garment_image(image_path: str) -> Image.Image:
    """
    Enhance garment image for better visibility in collages.
    
    Args:
        image_path: Path to garment image
    
    Returns:
        PIL Image: Enhanced image
    """
    try:
        img = Image.open(image_path).convert("RGBA")
        
        # Remove white background (simple approach)
        data = img.getdata()
        new_data = []
        for item in data:
            if item[:3] == (255, 255, 255):  # White pixel
                new_data.append((255, 255, 255, 0))  # Make transparent
            else:
                new_data.append(item)
        
        img.putdata(new_data)
        return img
    except:
        return Image.open(image_path).convert("RGBA")


def create_mix_match_suggestions(base_garment: Garment, matching_garments: List[Garment]) -> List[str]:
    """
    Create mix-and-match suggestion previews.
    
    Args:
        base_garment: Primary garment
        matching_garments: List of compatible garments
    
    Returns:
        List[str]: Paths to generated preview images
    """
    preview_paths = []
    
    for idx, garment in enumerate(matching_garments[:5]):  # Limit to 5 suggestions
        try:
            # Create a 2-item combination preview
            canvas = Image.new("RGB", (400, 300), color="white")
            
            base_path = os.path.join(UPLOAD_DIR, f"uploaded_{base_garment.filename}")
            match_path = os.path.join(UPLOAD_DIR, f"uploaded_{garment.filename}")
            
            if os.path.exists(base_path) and os.path.exists(match_path):
                base_img = Image.open(base_path).convert("RGBA")
                match_img = Image.open(match_path).convert("RGBA")
                
                base_img.thumbnail((150, 250), Image.Resampling.LANCZOS)
                match_img.thumbnail((150, 250), Image.Resampling.LANCZOS)
                
                canvas.paste(base_img, (25, 25), base_img)
                canvas.paste(match_img, (225, 25), match_img)
                
                output_path = os.path.join(PREVIEW_DIR, f"mix_match_{idx}.png")
                canvas.save(output_path)
                preview_paths.append(output_path)
        except Exception as e:
            print(f"Error creating mix-match preview: {e}")
    
    return preview_paths


def create_virtual_tryon_preview(garments: List[Garment], outfit_id: int):
    """
    Create a structured virtual try-on board.
    Returns tuple(path, used_items, missing_requirements).
    """
    if not garments:
        return None, [], ["No garments selected"]

    grouped = {"top": [], "bottom": [], "full_body": [], "footwear": [], "accessory": [], "other": []}
    for g in garments:
        grouped[category_group(g.category)].append(g)

    used = []
    missing = []
    use_full_body = len(grouped["full_body"]) > 0
    if use_full_body:
        used.append(grouped["full_body"][0])
    else:
        if grouped["top"]:
            used.append(grouped["top"][0])
        else:
            missing.append("Select at least one top")
        if grouped["bottom"]:
            used.append(grouped["bottom"][0])
        else:
            missing.append("Select at least one bottom")

    if grouped["footwear"]:
        used.append(grouped["footwear"][0])
    if grouped["accessory"]:
        used.append(grouped["accessory"][0])

    if missing:
        return None, used, missing

    # Canvas and mannequin
    canvas_w, canvas_h = 900, 1200
    canvas = Image.new("RGBA", (canvas_w, canvas_h), color="#edf2f8")
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle([220, 40, 680, 1140], radius=34, outline="#d8deea", width=3, fill="#ffffff")
    # Subtle torso silhouette only; avoid head/shape artifacts.
    draw.rounded_rectangle([340, 170, 560, 950], radius=92, fill="#f8fafe")
    draw.rounded_rectangle([356, 930, 544, 1090], radius=45, fill="#fafcff")

    center_x = canvas_w // 2
    waist_y = 565

    def _corner_samples(rgb_arr: np.ndarray):
        h, w, _ = rgb_arr.shape
        s = max(8, min(h, w) // 12)
        corners = [
            rgb_arr[0:s, 0:s],
            rgb_arr[0:s, w-s:w],
            rgb_arr[h-s:h, 0:s],
            rgb_arr[h-s:h, w-s:w],
        ]
        stacked = np.concatenate([c.reshape(-1, 3) for c in corners], axis=0)
        return stacked

    def trim_transparent_margins(img: Image.Image, min_alpha: int = 28, pad: int = 3) -> Image.Image:
        """Trim weak transparent halos and extra margins around product images."""
        rgba = np.array(img.convert("RGBA"))
        alpha = rgba[:, :, 3]
        ys, xs = np.where(alpha > min_alpha)
        if len(xs) == 0 or len(ys) == 0:
            return img
        x1, x2 = max(0, xs.min() - pad), min(alpha.shape[1], xs.max() + pad + 1)
        y1, y2 = max(0, ys.min() - pad), min(alpha.shape[0], ys.max() + pad + 1)
        return img.crop((x1, y1, x2, y2))

    def cleanup_garment(path: str) -> Image.Image:
        """
        Conservative cleanup:
        - If image already has transparency, keep it.
        - Remove background only when corners strongly indicate a plain backdrop.
        - Otherwise keep original to avoid block artifacts.
        """
        img = Image.open(path).convert("RGBA")
        rgba = np.array(img)
        alpha = rgba[:, :, 3]

        def safe_apply_alpha(rgba_arr: np.ndarray, candidate_alpha: np.ndarray) -> np.ndarray:
            """
            Guard against over-aggressive background removal.
            Revert if preserved area becomes unrealistically small.
            """
            h, w = candidate_alpha.shape
            keep = candidate_alpha > 20
            keep_ratio = float(np.mean(keep))
            ys, xs = np.where(keep)
            if len(xs) == 0 or len(ys) == 0:
                return np.full((h, w), 255, dtype=np.uint8)
            bbox_h = (ys.max() - ys.min() + 1) / max(1, h)
            bbox_w = (xs.max() - xs.min() + 1) / max(1, w)

            # Too little area or tiny bbox => likely wrong cutout for light garments.
            if keep_ratio < 0.12 or bbox_h < 0.36 or bbox_w < 0.22:
                return np.full((h, w), 255, dtype=np.uint8)
            return candidate_alpha

        # Respect existing transparency from uploaded PNGs.
        if np.mean(alpha < 255) > 0.02:
            out = Image.fromarray(rgba, "RGBA")
            return trim_transparent_margins(out, min_alpha=24, pad=2)

        rgb = rgba[:, :, :3].astype(np.int16)
        corners = _corner_samples(rgb.astype(np.uint8)).astype(np.int16)
        corner_med = np.median(corners, axis=0)
        corner_std = np.std(corners, axis=0).mean()

        # Decide if backdrop is likely plain.
        plain_backdrop = corner_std < 22
        if plain_backdrop:
            # Distance from corner median color.
            dist = np.sqrt(np.sum((rgb - corner_med) ** 2, axis=2))
            # Background candidate mask by color similarity.
            bg = dist < 32
            # Only apply if it covers a meaningful outer area.
            edge_band = 18
            edge_mask = np.zeros(bg.shape, dtype=bool)
            edge_mask[:edge_band, :] = True
            edge_mask[-edge_band:, :] = True
            edge_mask[:, :edge_band] = True
            edge_mask[:, -edge_band:] = True
            edge_bg_ratio = np.mean(bg[edge_mask])

            # Remove only when edges are mostly background.
            if edge_bg_ratio > 0.72:
                new_alpha = np.where(bg, 0, 255).astype(np.uint8)
                rgba[:, :, 3] = safe_apply_alpha(rgba, new_alpha)

                # Light feather on alpha to avoid hard jagged edges.
                feather = Image.fromarray(rgba[:, :, 3], "L").filter(ImageFilter.GaussianBlur(radius=1.2))
                rgba[:, :, 3] = np.array(feather)
        else:
            # Fallback for non-transparent JPEGs with plain/gradient backgrounds:
            # detect edge-connected background and knock it out.
            rgb_u8 = rgb.astype(np.uint8)
            h, w, _ = rgb_u8.shape
            border = np.concatenate([
                rgb_u8[0, :, :],
                rgb_u8[h - 1, :, :],
                rgb_u8[:, 0, :],
                rgb_u8[:, w - 1, :]
            ], axis=0).astype(np.int16)
            bg_med = np.median(border, axis=0)

            # Distance to estimated background color.
            dist = np.sqrt(np.sum((rgb.astype(np.int16) - bg_med) ** 2, axis=2))
            bg_candidate = dist < 34

            visited = np.zeros((h, w), dtype=bool)
            edge_bg = np.zeros((h, w), dtype=bool)
            q = deque()

            # Seed from borders.
            for x in range(w):
                if bg_candidate[0, x]:
                    q.append((0, x))
                if bg_candidate[h - 1, x]:
                    q.append((h - 1, x))
            for y in range(h):
                if bg_candidate[y, 0]:
                    q.append((y, 0))
                if bg_candidate[y, w - 1]:
                    q.append((y, w - 1))

            while q:
                y, x = q.popleft()
                if visited[y, x] or not bg_candidate[y, x]:
                    continue
                visited[y, x] = True
                edge_bg[y, x] = True
                if y > 0:
                    q.append((y - 1, x))
                if y < h - 1:
                    q.append((y + 1, x))
                if x > 0:
                    q.append((y, x - 1))
                if x < w - 1:
                    q.append((y, x + 1))

            if np.mean(edge_bg) > 0.18:
                new_alpha = np.where(edge_bg, 0, 255).astype(np.uint8)
                rgba[:, :, 3] = safe_apply_alpha(rgba, new_alpha)
                feather = Image.fromarray(rgba[:, :, 3], "L").filter(ImageFilter.GaussianBlur(radius=0.9))
                rgba[:, :, 3] = np.array(feather)

        out = Image.fromarray(rgba, "RGBA")
        return trim_transparent_margins(out, min_alpha=30, pad=2)

    def soften_alpha_edges(img: Image.Image, radius: float = 0.9) -> Image.Image:
        rgba = img.copy()
        alpha = rgba.split()[-1].filter(ImageFilter.GaussianBlur(radius=radius))
        rgba.putalpha(alpha)
        return rgba

    def feather_edge(img: Image.Image, edge: str = "bottom", band: int = 26, min_alpha: int = 170) -> Image.Image:
        rgba = img.copy().convert("RGBA")
        alpha = np.array(rgba.split()[-1], dtype=np.float32)
        h, w = alpha.shape
        band = max(8, min(band, h // 2))
        if edge == "bottom":
            for i in range(band):
                row = h - band + i
                factor = min_alpha + ((255 - min_alpha) * (i / max(1, band - 1)))
                alpha[row, :] = np.minimum(alpha[row, :], factor)
        elif edge == "top":
            for i in range(band):
                factor = min_alpha + ((255 - min_alpha) * (i / max(1, band - 1)))
                alpha[i, :] = np.minimum(alpha[i, :], factor)
        rgba.putalpha(Image.fromarray(alpha.clip(0, 255).astype(np.uint8), "L"))
        return rgba

    def paste_with_shadow(base: Image.Image, overlay: Image.Image, x: int, y: int):
        """Paste garment with a subtle realistic shadow."""
        alpha = overlay.split()[-1]
        shadow = Image.new("RGBA", overlay.size, color=(0, 0, 0, 85))
        shadow.putalpha(alpha)
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=4))
        base.alpha_composite(shadow, (x + 4, y + 6))
        base.alpha_composite(overlay, (x, y))

    # pick items by role
    top_item = next((g for g in used if category_group(g.category) == "top"), None)
    bottom_item = next((g for g in used if category_group(g.category) == "bottom"), None)
    full_item = next((g for g in used if category_group(g.category) == "full_body"), None)
    footwear_item = next((g for g in used if category_group(g.category) == "footwear"), None)
    accessory_item = next((g for g in used if category_group(g.category) == "accessory"), None)

    try:
        if full_item:
            img_path = os.path.join(UPLOAD_DIR, f"uploaded_{full_item.filename}")
            if os.path.exists(img_path):
                full = cleanup_garment(img_path)
                full.thumbnail((420, 860), Image.Resampling.LANCZOS)
                fx = center_x - full.width // 2
                fy = 150
                paste_with_shadow(canvas, full, fx, fy)

        else:
            prepared_bottom = None
            if bottom_item:
                img_path = os.path.join(UPLOAD_DIR, f"uploaded_{bottom_item.filename}")
                if os.path.exists(img_path):
                    bottom = cleanup_garment(img_path)
                    bottom = soften_alpha_edges(bottom)
                    bottom.thumbnail((335, 610), Image.Resampling.LANCZOS)
                    bottom = feather_edge(bottom, edge="top", band=max(16, bottom.height // 12), min_alpha=145)
                    prepared_bottom = bottom

            prepared_top = None
            if top_item:
                img_path = os.path.join(UPLOAD_DIR, f"uploaded_{top_item.filename}")
                if os.path.exists(img_path):
                    top = cleanup_garment(img_path)
                    top = soften_alpha_edges(top)

                    # Adaptive top sizing: align top width to selected bottom for realistic proportion.
                    if prepared_bottom is not None:
                        target_top_width = max(300, min(430, int(prepared_bottom.width * 1.12)))
                    else:
                        target_top_width = 360
                    top.thumbnail((target_top_width, 560), Image.Resampling.LANCZOS)

                    # Ensure very short/cropped tops are not rendered tiny.
                    if top.height < 220:
                        scale = 220 / max(1, top.height)
                        new_w = min(460, int(top.width * scale))
                        new_h = int(top.height * scale)
                        top = top.resize((new_w, new_h), Image.Resampling.LANCZOS)

                    # Match top presence to bottom scale so it doesn't look tiny.
                    if prepared_bottom is not None:
                        desired_top_h = int(prepared_bottom.height * 0.62)
                        if top.height < desired_top_h:
                            scale = desired_top_h / max(1, top.height)
                            new_w = min(470, int(top.width * scale))
                            new_h = int(top.height * scale)
                            top = top.resize((new_w, new_h), Image.Resampling.LANCZOS)

                    top = feather_edge(top, edge="bottom", band=max(18, top.height // 9), min_alpha=150)
                    prepared_top = top

            # Place garments with explicit, small waistband overlap.
            if prepared_bottom is not None and prepared_top is not None:
                bx = center_x - prepared_bottom.width // 2
                by = waist_y - int(prepared_bottom.height * 0.06)

                tx = center_x - prepared_top.width // 2
                desired_overlap = max(36, min(72, int(prepared_top.height * 0.12)))
                ty = max(100, by + desired_overlap - prepared_top.height)

                # Top first, bottom second so only waist area is covered.
                paste_with_shadow(canvas, prepared_top, tx, ty)
                paste_with_shadow(canvas, prepared_bottom, bx, by)
            elif prepared_top is not None:
                tx = center_x - prepared_top.width // 2
                ty = max(110, waist_y - int(prepared_top.height * 0.68))
                paste_with_shadow(canvas, prepared_top, tx, ty)
            elif prepared_bottom is not None:
                bx = center_x - prepared_bottom.width // 2
                by = waist_y - int(prepared_bottom.height * 0.06)
                paste_with_shadow(canvas, prepared_bottom, bx, by)

        if footwear_item:
            img_path = os.path.join(UPLOAD_DIR, f"uploaded_{footwear_item.filename}")
            if os.path.exists(img_path):
                shoe = cleanup_garment(img_path)
                shoe.thumbnail((220, 170), Image.Resampling.LANCZOS)
                sx = center_x - shoe.width // 2
                sy = 980
                paste_with_shadow(canvas, shoe, sx, sy)

        if accessory_item:
            img_path = os.path.join(UPLOAD_DIR, f"uploaded_{accessory_item.filename}")
            if os.path.exists(img_path):
                acc = cleanup_garment(img_path)
                acc.thumbnail((180, 180), Image.Resampling.LANCZOS)
                ax = 660
                ay = 200
                paste_with_shadow(canvas, acc, ax, ay)
    except Exception as e:
        print(f"Error creating realistic try-on layout: {e}")

    # Minimal legend
    legend_y = 1120
    labels = [f"{g.category} {g.color}" for g in used[:4]]
    draw.text((240, legend_y), " | ".join(labels), fill="#4a4f5e")

    output_path = os.path.join(PREVIEW_DIR, f"tryon_{outfit_id}.png")
    canvas.convert("RGB").save(output_path)
    return output_path, used, []
