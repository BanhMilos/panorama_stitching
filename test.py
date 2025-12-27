import re
import cv2
import numpy as np
import glob
import math
from pathlib import Path
import os

# ------------------ CONFIG ------------------

IMAGE_DIR = "./unconverted"
OUTPUT_FILE = "./output/panorama.jpg"

H_FOV_DEG = 60.0        # horizontal field of view of your camera
V_FOV_DEG = 40.0        # vertical field of view
YAW_STEP_DEG = 18.0     # how much you rotate between shots
PITCH_DEG = 25.0         # assume horizontal ring

# Panorama resolution
PANO_WIDTH = 4000
PANO_HEIGHT = 2000

# Blending parameters
FEATHER_WIDTH = 100     # width of feathering blend zone

# --------------------------------------------


def gaussian_feather(img, width):
    """Create Gaussian feathering mask for smooth blending"""
    h, w = img.shape[:2]
    mask = np.ones((h, w), dtype=np.float32)
    
    # Feather edges
    for x in range(width):
        alpha = x / float(width)
        mask[:, x] *= alpha
        mask[:, w - 1 - x] *= alpha
    
    return mask


def spherical_project(img, yaw_deg, pitch_deg, pano, weight):
    h, w = img.shape[:2]

    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    
    # Create feathering mask for smooth blending
    feather_mask = gaussian_feather(img, FEATHER_WIDTH)

    for y in range(h):
        for x in range(w):
            # normalize pixel to [-1,1]
            nx = (x / w - 0.5) * math.radians(H_FOV_DEG)
            ny = (y / h - 0.5) * math.radians(V_FOV_DEG)

            theta = yaw + nx
            phi = pitch + ny

            u = int((theta + math.pi) / (2 * math.pi) * PANO_WIDTH)
            v = int((math.pi / 2 - phi) / math.pi * PANO_HEIGHT)

            if 0 <= u < PANO_WIDTH and 0 <= v < PANO_HEIGHT:
                pixel_weight = feather_mask[y, x]
                pano[v, u] += img[y, x] * pixel_weight
                weight[v, u] += pixel_weight


def blend_seams(pano, weight):
    """Apply multi-band blending to reduce seams"""
    # Normalize weight
    weight[weight == 0] = 1
    
    # Simple Gaussian blur to smooth transitions
    blurred = cv2.GaussianBlur(pano, (5, 5), 0)
    
    # Create smooth transition zones
    weight_normalized = weight[..., None]
    result = pano / weight_normalized
    
    return result


def main():
    image_paths = sorted(glob.glob(str(Path(IMAGE_DIR) / "*.jpg")))
    print(f"Found {len(image_paths)} images")

    if len(image_paths) < 2:
        raise RuntimeError("Need at least 2 images")

    pano = np.zeros((PANO_HEIGHT, PANO_WIDTH, 3), np.float32)
    weight = np.zeros((PANO_HEIGHT, PANO_WIDTH), np.float32)
    def extract_number(path):
        name = os.path.basename(path)
        m = re.search(r'\d+', name)
        return int(m.group()) if m else 0

    image_paths.sort(key=extract_number)    
    for i, path in enumerate(image_paths):
        img = cv2.imread(path)
        if img is None:
            print(f"Skipping {path}")
            continue

        yaw = i * YAW_STEP_DEG
        print(f"Projecting {path} at yaw={yaw:.1f}°")

        spherical_project(img, yaw, PITCH_DEG, pano, weight)

    # Advanced blending
    pano = blend_seams(pano, weight)
    
    # Clip and convert to uint8
    pano = np.clip(pano, 0, 255).astype(np.uint8)
    
    # Apply bilateral filter for edge-preserving smoothing
    pano = cv2.bilateralFilter(pano, 9, 75, 75)

    Path("./output").mkdir(exist_ok=True)
    cv2.imwrite(OUTPUT_FILE, pano)
    print(f"Saved panorama to {OUTPUT_FILE}")

    cv2.imshow("Panorama", pano)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
