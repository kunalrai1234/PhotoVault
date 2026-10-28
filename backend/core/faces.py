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
        print(f"[Faces] cv2_imread_safe error on {image_path}: {e}")
        return None

class FaceEngine:
    """
    Local-first face detection and recognition engine.
    Uses OpenCV YuNet for face detection and OpenCV SFace for 128-d embeddings.
    Runs 100% on CPU without cloud dependencies.
    """

    def __init__(self, models_dir: str = "assets/models"):
        self.models_dir = models_dir
        self.yunet_path = os.path.join(models_dir, "face_detection_yunet_2023mar.onnx")
        self.sface_path = os.path.join(models_dir, "face_recognition_sface_2021dec.onnx")
        
        self.detector: Optional[Any] = None
        self.recognizer: Optional[Any] = None
        self.is_enabled = True
        
        self.clusters: Dict[str, Dict[str, Any]] = {}
        self.face_metadata: Dict[str, Dict[str, Any]] = {}

        self._init_models()

    def _init_models(self) -> None:
        if os.path.exists(self.yunet_path):
            try:
                self.detector = cv2.FaceDetectorYN.create(
                    self.yunet_path, "", (320, 320), 0.7, 0.3, 5000
                )
                print("[FaceEngine] OpenCV YuNet face detector loaded.")
            except Exception as e:
                print(f"[FaceEngine] YuNet detector failed to load: {e}")

        if os.path.exists(self.sface_path):
            try:
                self.recognizer = cv2.FaceRecognizerSF.create(self.sface_path, "")
                print("[FaceEngine] OpenCV SFace face recognizer loaded.")
            except Exception as e:
                print(f"[FaceEngine] SFace recognizer failed to load: {e}")

    def detect_faces(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Detects faces in an image and extracts normalized embeddings.
        Downscales high-resolution images to max 640px for blazing-fast CPU inference.
        """
        if not self.is_enabled:
            return []

        if not os.path.exists(image_path):
            return []

        try:
            img = cv2_imread_safe(image_path)
            if img is None:
                return []

            orig_h, orig_w = img.shape[:2]
            faces_found: List[Dict[str, Any]] = []

            if self.detector is not None:
                # Downsample for detection if image is large (> 640px)
                max_dim = max(orig_w, orig_h)
                scale = 1.0
                if max_dim > 640:
                    scale = 640.0 / max_dim
                    detect_w = int(orig_w * scale)
                    detect_h = int(orig_h * scale)
                    detect_img = cv2.resize(img, (detect_w, detect_h))
                else:
                    detect_w, detect_h = orig_w, orig_h
                    detect_img = img

                self.detector.setInputSize((detect_w, detect_h))
                _, faces = self.detector.detect(detect_img)

                if faces is not None:
                    inv_scale = 1.0 / scale
                    for idx, face_data in enumerate(faces):
                        # Scale coordinates back to original image
                        box = [
                            int(face_data[0] * inv_scale),
                            int(face_data[1] * inv_scale),
                            int(face_data[2] * inv_scale),
                            int(face_data[3] * inv_scale)
                        ]
                        score = float(face_data[-1])

                        # Un-scale face landmarks for SFace alignment
                        orig_face_data = face_data.copy()
                        orig_face_data[:4] = [box[0], box[1], box[2], box[3]]
                        for p_idx in range(4, 14, 2):
                            orig_face_data[p_idx] = face_data[p_idx] * inv_scale
                            orig_face_data[p_idx + 1] = face_data[p_idx + 1] * inv_scale

                        # Extract embedding if recognizer available
                        embedding = None
                        if self.recognizer is not None:
                            try:
                                aligned_face = self.recognizer.alignCrop(img, orig_face_data)
                                raw_feat = self.recognizer.feature(aligned_face)
                                norm_feat = raw_feat / np.linalg.norm(raw_feat)
                                embedding = norm_feat.flatten().tolist()
                            except Exception as e:
                                print(f"[FaceEngine] Error extracting face feature: {e}")

                        # Fallback heuristic embedding
                        if embedding is None:
                            x, y, bw, bh = max(0, box[0]), max(0, box[1]), box[2], box[3]
                            face_crop = img[y:y+bh, x:x+bw]
                            if face_crop.size > 0:
                                resized = cv2.resize(face_crop, (32, 32))
                                gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                                feat = gray.astype(np.float32).flatten()
                                embedding = (feat / (np.linalg.norm(feat) + 1e-7)).tolist()

                        face_id = f"{os.path.basename(image_path)}_face_{idx}"
                        face_info = {
                            "face_id": face_id,
                            "image_path": image_path,
                            "box": box,
                            "confidence": round(score, 4),
                            "embedding": embedding
                        }
                        faces_found.append(face_info)
                        self.face_metadata[face_id] = face_info

            return faces_found

        except Exception as e:
            print(f"[FaceEngine] Error processing faces for {image_path}: {e}")
            return []

    def cluster_faces(self, threshold: float = 0.363) -> List[Dict[str, Any]]:
        all_face_ids = [fid for fid, f in self.face_metadata.items() if f.get("embedding")]
        n = len(all_face_ids)
        if n == 0:
            return []

        embeddings = np.array([self.face_metadata[fid]["embedding"] for fid in all_face_ids])
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normed_emb = embeddings / np.maximum(norms, 1e-7)
        similarity_matrix = np.dot(normed_emb, normed_emb.T)
        distance_matrix = 1.0 - similarity_matrix

        parent = list(range(n))
        def find(i):
            path = []
            while parent[i] != i:
                path.append(i)
                i = parent[i]
            for node in path:
                parent[node] = i
            return i

        def union(i, j):
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                parent[root_i] = root_j

        for i in range(n):
            for j in range(i + 1, n):
                if distance_matrix[i, j] <= threshold:
                    union(i, j)

        groups: Dict[int, List[str]] = {}
        for i in range(n):
            root = find(i)
            groups.setdefault(root, []).append(all_face_ids[i])

        person_clusters = []
        cluster_counter = 1
        unknown_faces: List[Dict[str, Any]] = []

        for root, fids in groups.items():
            faces_in_group = [self.face_metadata[fid] for fid in fids]
            unique_photos = list({f["image_path"] for f in faces_in_group})

            if len(faces_in_group) > 1:
                cluster_id = f"person_{cluster_counter:02d}"
                name = f"Person {cluster_counter:02d}"
                cluster_data = {
                    "cluster_id": cluster_id,
                    "name": name,
                    "face_count": len(faces_in_group),
                    "photo_count": len(unique_photos),
                    "photos": unique_photos,
                    "faces": faces_in_group,
                    "representative_face": faces_in_group[0]
                }
                self.clusters[cluster_id] = cluster_data
                person_clusters.append(cluster_data)
                cluster_counter += 1
            else:
                unknown_faces.extend(faces_in_group)

        if unknown_faces:
            unknown_photos = list({f["image_path"] for f in unknown_faces})
            person_clusters.append({
                "cluster_id": "person_unknown",
                "name": "Unknown / Unmatched",
                "face_count": len(unknown_faces),
                "photo_count": len(unknown_photos),
                "photos": unknown_photos,
                "faces": unknown_faces,
                "representative_face": unknown_faces[0] if unknown_faces else None
            })

        return person_clusters

    def rename_cluster(self, cluster_id: str, new_name: str) -> bool:
        if cluster_id in self.clusters:
            self.clusters[cluster_id]["name"] = new_name
            return True
        return False

    def merge_clusters(self, target_cluster_id: str, source_cluster_id: str) -> bool:
        if target_cluster_id in self.clusters and source_cluster_id in self.clusters:
            src = self.clusters[source_cluster_id]
            tgt = self.clusters[target_cluster_id]
            tgt["faces"].extend(src["faces"])
            tgt["photos"] = list(set(tgt["photos"] + src["photos"]))
            tgt["face_count"] = len(tgt["faces"])
            tgt["photo_count"] = len(tgt["photos"])
            del self.clusters[source_cluster_id]
            return True
        return False

    def delete_face_data(self) -> None:
        self.clusters.clear()
        self.face_metadata.clear()
