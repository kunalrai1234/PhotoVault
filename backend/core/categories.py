import os
import cv2
import numpy as np
from typing import List, Dict, Any, Optional

def cv2_imread_safe(image_path: str) -> Optional[np.ndarray]:
    """Safe image reader handling Windows Unicode/non-ASCII paths seamlessly."""
    try:
        with open(image_path, "rb") as f:
            chunk = f.read()
        arr = np.frombuffer(chunk, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"[Categories] cv2_imread_safe error on {image_path}: {e}")
        return None

CATEGORIES = [
    "People",
    "Selfies",
    "Family/Group Photos",
    "Travel",
    "Nature",
    "Mountains",
    "Beaches",
    "Food",
    "Animals",
    "Vehicles",
    "Documents",
    "Screenshots",
    "Events",
    "Other"
]

class LocalCategorizer:
    """
    Categorizes images locally using visual features, face detection,
    color space analysis (HSV), edge density, aspect ratio, and composition rules.
    Runs 100% offline with zero cloud dependency.
    """

    def __init__(self):
        pass

    def categorize_image(self, photo: Dict[str, Any], faces: List[Dict[str, Any]] = None) -> List[str]:
        tags: List[str] = []
        image_path = photo.get("path", "")
        if not os.path.exists(image_path):
            return ["Other"]

        w = photo.get("width", 0)
        h = photo.get("height", 0)
        ext = photo.get("extension", "").lower()
        fname = photo.get("filename", "").lower()

        # 1. Screenshot detection
        screen_ratios = [16/9, 16/10, 19.5/9, 20/9, 4/3]
        if w > 0 and h > 0:
            aspect = max(w, h) / min(w, h)
            is_screen_ratio = any(abs(aspect - r) < 0.05 for r in screen_ratios)
            if ("screenshot" in fname or "screen_shot" in fname or "capture" in fname) or (ext == ".png" and is_screen_ratio and (w in (1920, 2560, 3840, 1080, 1280) or h in (1920, 2560, 3840, 1080, 1280))):
                tags.append("Screenshots")

        # 2. People & Family / Group photos
        detected_faces = faces if faces is not None else photo.get("faces", [])
        face_count = len(detected_faces)

        if face_count == 1:
            tags.append("People")
            box = detected_faces[0].get("box", [0, 0, 0, 0])
            face_area = box[2] * box[3]
            img_area = max(1, w * h)
            if (face_area / img_area) > 0.08:
                tags.append("Selfies")
        elif face_count >= 2:
            tags.append("People")
            tags.append("Family/Group Photos")

        # 3. Computer Vision Color & Edge Analysis
        try:
            img = cv2_imread_safe(image_path)
            if img is not None:
                small = cv2.resize(img, (160, 160))
                hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

                green_mask = cv2.inRange(hsv, (35, 40, 40), (85, 255, 255))
                green_ratio = np.count_nonzero(green_mask) / (160 * 160)

                blue_mask = cv2.inRange(hsv, (90, 50, 50), (135, 255, 255))
                blue_ratio = np.count_nonzero(blue_mask) / (160 * 160)

                warm_mask = cv2.inRange(hsv, (0, 70, 70), (25, 255, 255))
                warm_ratio = np.count_nonzero(warm_mask) / (160 * 160)

                edges = cv2.Canny(gray, 50, 150)
                edge_density = np.count_nonzero(edges) / (160 * 160)
                white_pixels = np.count_nonzero(gray > 200) / (160 * 160)

                if white_pixels > 0.65 and 0.04 < edge_density < 0.25 and face_count == 0:
                    tags.append("Documents")

                if green_ratio > 0.22:
                    tags.append("Nature")

                if blue_ratio > 0.25:
                    if green_ratio > 0.10:
                        tags.append("Mountains")
                    else:
                        tags.append("Beaches")
                        tags.append("Travel")

                if warm_ratio > 0.30 and face_count == 0 and "Screenshots" not in tags:
                    tags.append("Food")

        except Exception as e:
            print(f"[Categorizer] Error reading visual features for {image_path}: {e}")

        if not tags:
            tags.append("Other")

        return list(dict.fromkeys(tags))
