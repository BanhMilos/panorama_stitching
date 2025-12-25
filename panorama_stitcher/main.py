import cv2
import numpy as np
import img_convert
import sys
import json
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
unconverted_dir = SCRIPT_DIR / "../unconverted"
output_dir = SCRIPT_DIR / "../output"

def main():

    def delete_old_input():
        for file_path in unconverted_dir.iterdir():
            if file_path.is_file():  
                file_path.unlink()
    print("uncoverted_dir", unconverted_dir)
    image_unconverted_paths = [
        str(p) for p in (
            list(unconverted_dir.glob("*.jpg")) +
            list(unconverted_dir.glob("*.png")) +
            list(unconverted_dir.glob("*.jpeg")) +
            list(unconverted_dir.glob("*.webp"))
        )
    ]    
    imgs = []
    if (len(image_unconverted_paths) < 2):
        print(
        
        json.dumps({'result' : "failed", "reason":"Need at least two images to stitch a panorama."})
        )
        delete_old_input()
        sys.exit(1)
    imgsByte = img_convert.convert_image_list_to_jpg_bytes(image_unconverted_paths,quality=95)

    for i, data in enumerate(imgsByte):
        if data is None or len(data) == 0:
            print(json.dumps({'result': 'failed', 'reason': f'Image {i} byte buffer is empty'}))
            sys.exit(1)

        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)

        if img is None:
            print(json.dumps({'result': 'failed', 'reason': f'Image {i} could not be decoded'}))
            sys.exit(1)

        h, w = img.shape[:2]
        if h == 0 or w == 0:
            print(json.dumps({'result': 'failed', 'reason': f'Image {i} has invalid size {w}x{h}'}))
            sys.exit(1)

        imgs.append(img)


    stitcher=cv2.Stitcher.create()
    (status,output)=stitcher.stitch(imgs)


    if status != cv2.Stitcher_OK:
        print(
        json.dumps({'result' : "failed", "reason": str(status)})
        )
        delete_old_input()
        sys.exit(1)

    output_path = output_dir / "panorama.jpg"
    mkdir_cmd = f"mkdir -p {output_path.parent}"
    os.system(mkdir_cmd)
    cv2.imwrite(output_path,output)
    print(
    json.dumps({'result' : "success", "output_path": str(output_path)})
    )
    #delete_old_input()
    sys.exit(0)    
    
if __name__ == "__main__":
    main()
