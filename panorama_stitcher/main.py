from stitching import Stitcher
import glob
from pathlib import Path
import panorama_split

SCRIPT_DIR = Path(__file__).resolve().parent
unconverted_dir = SCRIPT_DIR / "../unconverted"
output_dir = SCRIPT_DIR / "../output"
image_paths = glob.glob(str(unconverted_dir / "*.jpg"))

print("Found images:", image_paths)

if len(image_paths) < 2:
    raise RuntimeError("Need at least 2 images to stitch")

stitcher = Stitcher(detector="sift", confidence_threshold=0.3, matches_graph_dot_file = "matches.dot")
panorama = stitcher.stitch(image_paths)
import cv2
panorama = cv2.resize(panorama, (2048, 1024), interpolation=cv2.INTER_CUBIC)
cv2.imshow("Panorama", panorama)
cv2.imwrite(str(output_dir / "panorama.jpg"), panorama)
panorama_split.split_panorama_file_to_faces(
    panorama_path=output_dir / "panorama.jpg",
    save_dir=output_dir,
    face_size=1024)
cv2.waitKey(0)
cv2.destroyAllWindows()
