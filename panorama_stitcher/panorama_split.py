import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Union


def _face_dirs(face: str, a: np.ndarray, b: np.ndarray):
	"""Return direction vectors (x, y, z) for the given face using coordinates a, b in [-1, 1]."""
	if face == "front":
		x, y, z = a, b, np.ones_like(a)
	elif face == "back":
		x, y, z = -a, b, -np.ones_like(a)
	elif face == "right":
		x, y, z = np.ones_like(a), b, -a
	elif face == "left":
		x, y, z = -np.ones_like(a), b, a
	elif face == "top":
		x, y, z = a, np.ones_like(a), -b
	elif face == "bottom":
		x, y, z = a, -np.ones_like(a), b
	else:
		raise ValueError(f"Unknown face: {face}")
	return x, y, z


def _build_uv_map_for_face(face: str, size: int, width: int, height: int) -> tuple[np.ndarray, np.ndarray]:
	"""Build equirectangular UV sampling map for a cube face."""
	# Pixel centers in [-1, 1]
	xs = (np.arange(size, dtype=np.float32) + 0.5) / size * 2.0 - 1.0
	ys = (np.arange(size, dtype=np.float32) + 0.5) / size * 2.0 - 1.0
	a, b = np.meshgrid(xs, ys)  # a: horizontal, b: vertical

	x, y, z = _face_dirs(face, a, b)
	norm = np.sqrt(x * x + y * y + z * z)
	x /= norm
	y /= norm
	z /= norm

	lon = np.arctan2(x, z)  # [-pi, pi]
	lat = np.arcsin(np.clip(y, -1.0, 1.0))  # [-pi/2, pi/2]

	u = (lon + np.pi) / (2.0 * np.pi) * width
	v = (lat + np.pi / 2.0) / np.pi * height

	# Wrap horizontally, clamp vertically
	u = np.mod(u, float(width))
	v = np.clip(v, 0.0, float(height - 1))

	return u.astype(np.float32), v.astype(np.float32)


def split_panorama_to_faces(equirect_img: np.ndarray, face_size: Optional[int] = None) -> Dict[str, np.ndarray]:
	"""
	Split an equirectangular panorama image into cube faces.

	Returns a dict with keys: left, right, top, bottom, front, back.
	"""
	h, w = equirect_img.shape[:2]
	if face_size is None:
		# typical equirect: w = 2N, h = N -> use min(h, w//2)
		face_size = max(1, min(h, w // 2))

	faces = ["left", "right", "top", "bottom", "front", "back"]
	out: Dict[str, np.ndarray] = {}
	for face in faces:
		map_x, map_y = _build_uv_map_for_face(face, face_size, w, h)
		face_img = cv2.remap(equirect_img, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
		out[face] = face_img

	return out


def split_panorama_file_to_faces(panorama_path: Union[str, Path], save_dir: Union[str, Path], face_size: Optional[int] = None) -> Dict[str, str]:
	"""
	Load a panorama image from disk, split into faces, and save as JPEGs.
	Returns a dict mapping face name to saved file path.
	"""
	panorama_path = Path(panorama_path)
	save_dir = Path(save_dir)
	save_dir.mkdir(parents=True, exist_ok=True)

	img = cv2.imread(str(panorama_path))
	if img is None:
		raise ValueError(f"Unable to read panorama image: {panorama_path}")

	faces = split_panorama_to_faces(img, face_size=face_size)

	base_name = panorama_path.stem
	saved: Dict[str, str] = {}
	for name, face_img in faces.items():
		out_path = save_dir / f"{base_name}_{name}.jpg"
		cv2.imwrite(str(out_path), face_img)
		saved[name] = str(out_path)

	return saved
