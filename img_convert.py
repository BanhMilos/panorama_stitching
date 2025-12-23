from io import BytesIO
import os
from typing import Iterable, List, Optional, Union
from PIL import Image, ImageOps

# to convert heic images (ios supremacy)
try:
    import pillow_heif  

    pillow_heif.register_heif_opener()
except Exception:
    pass


ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".heic",
    ".heif",
}

# check if the file is an image
def _is_image_file(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in ALLOWED_EXTENSIONS

# convert a single image to jpg bytes
def convert_image_to_jpg_bytes(input_file: str, quality: int = 95) -> bytes:
    with Image.open(input_file) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode != "RGB":
            im = im.convert("RGB")

        buffer = BytesIO()
        im.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=True)
        return buffer.getvalue()

# convert a list of images to jpg bytes
def convert_image_list_to_jpg_bytes(
    input_files: Iterable[str], quality: int = 95
) -> List[bytes]:
    converted_images = []
    for input_file in input_files:
        if not _is_image_file(input_file):
            raise ValueError(f"Unsupported image format: {input_file}")
        jpg_bytes = convert_image_to_jpg_bytes(input_file, quality=quality)
        converted_images.append(jpg_bytes)
    return converted_images