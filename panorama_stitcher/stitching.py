import cv2
from typing import List, Tuple, Optional
import numpy as np
import warnings


def _validate_images(imgs: List[np.ndarray]) -> Optional[str]:
    """Validate image list for stitching. Returns error message if invalid, None if valid."""
    if not imgs:
        return "Image list is empty"
    if len(imgs) < 2:
        return "Need at least 2 images for stitching"
    
    for i, img in enumerate(imgs):
        if img is None:
            return f"Image {i} is None"
        if not isinstance(img, np.ndarray):
            return f"Image {i} is not a numpy array"
        if img.size == 0:
            return f"Image {i} is empty"
        if not np.isfinite(img).all():
            return f"Image {i} contains invalid values (NaN/Inf)"
        
        h, w = img.shape[:2]
        if h < 20 or w < 20:
            return f"Image {i} is too small ({w}x{h}). Minimum 20x20"
        if h > 8000 or w > 8000:
            return f"Image {i} is too large ({w}x{h}). Maximum 8000x8000"
    
    return None


def _prepare_images_for_stitching(imgs: List[np.ndarray]) -> List[np.ndarray]:
    """Prepare images for stitching: ensure uint8 type and valid channels."""
    prepared = []
    for img in imgs:
        # Ensure uint8
        if img.dtype != np.uint8:
            if img.dtype in [np.float32, np.float64]:
                img = np.clip(img * 255, 0, 255).astype(np.uint8)
            else:
                img = img.astype(np.uint8)
        
        # Ensure 3 channels (BGR) or convert grayscale
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        elif img.shape[2] != 3:
            continue  # Skip invalid channels
        
        prepared.append(img)
    
    return prepared


def stitch_images(imgs: List[np.ndarray]) -> Tuple[int, np.ndarray]:
    """Stitch the given list of images using OpenCV's Stitcher.

    Returns (status, panorama_image). status values:
    - 0 (OK): Success
    - 1 (ERR_NEED_MORE_IMGS): Not enough images
    - 2 (ERR_HOMOGRAPHY_EST_FAIL): Feature matching failed
    - 3 (ERR_CAMERA_PARAMS_ADJUST_FAIL): Camera params adjustment failed
    
    Configured for maximum success rate, even if sacrificing quality.
    """
    # Validate input
    error = _validate_images(imgs)
    if error:
        print(f"[Stitching Error] {error}")
        return -1, np.array([])
    
    # Prepare images
    imgs = _prepare_images_for_stitching(imgs)
    if len(imgs) < 2:
        print("[Stitching Error] After preparation, fewer than 2 valid images remain")
        return -1, np.array([])
    
    try:
        # Suppress OpenCV warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # Try high-quality stitching first
            stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)
            
            # Configure for maximum success rate
            # Lower resolutions = faster processing, more forgiving feature matching
            stitcher.setRegistrationResol(0.6)      # Lower resolution for registration (default ~0.6)
            stitcher.setSeamEstimationResol(0.1)    # Very low for seam estimation
            stitcher.setCompositingResol(0.3)       # Lower resolution for compositing
            
            # Lower confidence threshold = accept weaker matches
            stitcher.setPanoConfidenceThresh(0.3)   # Very lenient (default ~1.0)
            
            # Disable wave correction = faster, less strict
            stitcher.setWaveCorrection(False)
            
            # Use fastest interpolation
            stitcher.setInterpolationFlags(cv2.INTER_LINEAR)
            
            status, output = stitcher.stitch(imgs)
            
            # If still fails, try even more aggressive settings
            if status != cv2.Stitcher_OK:
                print(f"[Stitching] Standard config failed (status {status}), retrying with ultra-lenient settings...")
                stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)
                stitcher.setRegistrationResol(0.4)
                stitcher.setSeamEstimationResol(0.05)
                stitcher.setCompositingResol(0.2)
                stitcher.setPanoConfidenceThresh(0.1)
                stitcher.setWaveCorrection(False)
                stitcher.setInterpolationFlags(cv2.INTER_LINEAR)
                
                status, output = stitcher.stitch(imgs)
            
            return status, output
    
    except cv2.error as e:
        print(f"[Stitching OpenCV Error] {e}")
        return -1, np.array([])
    except Exception as e:
        print(f"[Stitching Unexpected Error] {e}")
        return -1, np.array([])
