import cv2
import numpy as np
import glob
import img_convert
import sys
import json
import os

def main():
    image_unconverted_paths = glob.glob("unconverted/*.HEIC")
    imgs = []

    if (len(image_unconverted_paths) < 2):
        json.dumps({'result' : "failed", "reason":"Need at least two images to stitch a panorama."})
        sys.exit(1)
    imgsByte = img_convert.convert_image_list_to_jpg_bytes(image_unconverted_paths,quality=95)

    for i in range(len(imgsByte)):
        img = cv2.imdecode(np.frombuffer(imgsByte[i], np.uint8), cv2.IMREAD_COLOR)
        if (img is None):
            json.dumps({'result' : "failed", "reason":f"Image at {image_unconverted_paths[i]} could not be read."})
            sys.exit(1)
        imgs.append(img)

    stitcer=cv2.Stitcher.create()
    (status,output)=stitcer.stitch(imgs)

    if status != cv2.Stitcher_OK:
        json.dumps({'result' : "failed", "reason": int(status)})
        sys.exit(1)

    output_path = "output/panorama.jpg"
    mkdir_cmd = "mkdir -p output"
    os.system(mkdir_cmd)
    cv2.imwrite(output_path,output)
    json.dumps({'result' : "success", "output_path": output_path})
    sys.exit(0)    
    
if __name__ == "__main__":
    main()