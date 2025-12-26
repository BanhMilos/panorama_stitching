import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import img_convert

SUPPORTED_PATTERNS = ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp", "*.tif", "*.tiff", "*.heic", "*.heif"]


def find_image_paths(folder: Path) -> List[str]:
    paths: List[str] = []
    for pattern in SUPPORTED_PATTERNS:
        for p in folder.glob(pattern):
            paths.append(str(p))
    return sorted(paths)


def load_and_validate_images(unconverted_dir: Path) -> Tuple[List[np.ndarray], Optional[str]]:
    """
    - Discovers images in the provided folder.
    - Requires at least two images.
    - Converts to JPEG bytes and decodes to OpenCV images.
    - Validates each image buffer and dimensions.

    Returns (images, error_reason). If error_reason is not None, images will be empty.
    """
    image_paths = find_image_paths(unconverted_dir)
    if len(image_paths) < 2:
        return [], "Need at least two images to stitch a panorama."

    try:
        imgs_bytes = img_convert.convert_image_list_to_jpg_bytes(image_paths, quality=95)
    except Exception as e:
        return [], f"Image conversion failed: {e}"

    imgs: List[np.ndarray] = []
    for i, data in enumerate(imgs_bytes):
        if data is None or len(data) == 0:
            return [], f"Image {i} byte buffer is empty"

        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        # if img is None:
        #     return [], f"Image {i} could not be decoded"

        # h, w = img.shape[:2]
        # if h == 0 or w == 0:
        #     return [], f"Image {i} has invalid size {w}x{h}"

        imgs.append(img)

    return imgs, None
