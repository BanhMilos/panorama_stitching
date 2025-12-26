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

def main():

    def delete_old_input():
        for file_path in unconverted_dir.iterdir():
            if file_path.is_file():
                file_path.unlink()

    print("uncoverted_dir", unconverted_dir)

    # Load and validate input images using the validation module
    imgs, error = input_validation.load_and_validate_images(unconverted_dir)
    if error:
        print(json.dumps({'result': 'failed', 'reason': error}))
        #delete_old_input()
        sys.exit(1)

    # Stitch images using the stitching module
    status, output = stitching.stitch_images(imgs)

    if status != cv2.Stitcher_OK:
        print(json.dumps({'result': 'failed', 'reason': str(status)}))
        #delete_old_input()
        sys.exit(1)

    # Save panorama output
    output_path = output_dir / "panorama.jpg"
    mkdir_cmd = f"mkdir -p {output_path.parent}"
    os.system(mkdir_cmd)
    cv2.imwrite(str(output_path), output)

    # Split panorama into cube faces on success and save them alongside the panorama
    face_paths = panorama_split.split_panorama_file_to_faces(output_path, output_path.parent)

    print(json.dumps({'result': 'success', 'output_path': str(output_path), 'face_paths': face_paths}))
    # delete_old_input() # Uncomment if input files should be cleared on success
    sys.exit(0)
    
if __name__ == "__main__":
    main()
