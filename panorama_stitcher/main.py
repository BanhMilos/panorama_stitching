import cv2
import numpy as np
import sys
import json
import os
from pathlib import Path
import panorama_split
import input_validation
import stitching

SCRIPT_DIR = Path(__file__).resolve().parent
unconverted_dir = SCRIPT_DIR / "../unconverted"
output_dir = SCRIPT_DIR / "../output"
MAX_DIM = 1600 

def main():

    def delete_old_input():
        for file_path in unconverted_dir.iterdir():
            if file_path.is_file():
                file_path.unlink()

    print("uncoverted_dir", unconverted_dir)

    # Load and validate 
    imgs, error = input_validation.load_and_validate_images(unconverted_dir)
    if error:
        print(json.dumps({'result': 'failed', 'reason': error}))
        #delete_old_input()
        sys.exit(1)
    for i, img in enumerate(imgs):
        if not np.isfinite(img).all():
            img = np.nan_to_num(img)

        h, w = img.shape[:2]
        scale = min(MAX_DIM / w, MAX_DIM / h, 1.0)
        if scale < 1.0:
            img = cv2.resize(img, (int(w * scale), int(h * scale)))
        imgs[i] = img
    # Stitch
    status, output = stitching.stitch_images(imgs)

    if status != cv2.Stitcher_OK:
        status_map = {
            -1: "Validation or processing error",
            0: "OK",
            1: "Need more images",
            2: "Homography estimation failed",
            3: "Camera parameters adjustment failed"
        }
        reason = status_map.get(status, f"Unknown error (code {status})")
        print(json.dumps({'result': 'failed', 'reason': reason}))
        #delete_old_input()
        sys.exit(1)
    
    if output is None or output.size == 0:
        print(json.dumps({'result': 'failed', 'reason': 'Stitching produced empty output'}))
        sys.exit(1)

    # Save panorama output
    output_path = output_dir / "panorama.jpg"
    mkdir_cmd = f"mkdir -p {output_path.parent}"
    os.system(mkdir_cmd)
    cv2.imwrite(str(output_path), output)

    # Split panorama into cube faces
    face_paths = panorama_split.split_panorama_file_to_faces(output_path, output_path.parent)

    print(json.dumps({'result': 'success', 'output_path': str(output_path), 'face_paths': face_paths}))
    # delete_old_input() 
    sys.exit(0)
    
if __name__ == "__main__":
    main()
