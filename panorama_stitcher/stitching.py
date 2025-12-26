import cv2
from typing import List, Tuple
import numpy as np


def stitch_images(imgs: List[np.ndarray]) -> Tuple[int, np.ndarray]:
    """Stitch the given list of images using OpenCV's Stitcher.

    Returns (status, panorama_image).
    """
    stitcher = cv2.Stitcher.create()
    status, output = stitcher.stitch(imgs)
    return status, output
