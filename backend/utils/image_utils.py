from PIL import Image
import numpy as np
from rembg import remove

def get_dominant_color(image_path):
    with Image.open(image_path).convert("RGBA") as im:
        img_no_bg = remove(im)

    arr = np.array(img_no_bg)
    mask = arr[..., 3] > 0
    rgb_pixels = arr[mask][:, :3]
    if rgb_pixels.size == 0:
        rgb_pixels = arr[..., :3].reshape(-1, 3)
    avg_color = rgb_pixels.mean(axis=0)
    return '#%02x%02x%02x' % (int(avg_color[0]), int(avg_color[1]), int(avg_color[2]))