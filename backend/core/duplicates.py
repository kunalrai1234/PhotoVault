import hashlib
import os
from typing import Dict, List, Any

def compute_sha256(file_path: str, chunk_size: int = 65536) -> str:
    """
    Computes cryptographic SHA-256 hash using chunked streaming.
    Memory safe even for 100MB+ RAW/TIFF files.
    """
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"[Duplicates] Error hashing {file_path}: {e}")
        return ""

class ExactDuplicateEngine:
    """
    Detects true duplicates based solely on content SHA-256.
    Uses file size as an optional pre-filter to bypass expensive hashing on unique files.
    """

    def __init__(self):
        pass

    def find_duplicates(self, photos: List[Dict[str, Any]], progress_callback=None) -> List[Dict[str, Any]]:
        """
        Groups photos by exact SHA-256 hash.
        Only items with 2+ occurrences are returned in duplicate groups.
        """
        # Step 1: Group by file size to identify collision candidates
        size_buckets: Dict[int, List[Dict[str, Any]]] = {}
        for photo in photos:
            sz = photo.get("size", 0)
            if sz > 0:
                size_buckets.setdefault(sz, []).append(photo)

        # Step 2: Only files sharing sizes need hash computation (if not already cached)
        candidate_count = sum(len(items) for items in size_buckets.values() if len(items) > 1)
        processed = 0

        hash_buckets: Dict[str, List[Dict[str, Any]]] = {}

        for size, items in size_buckets.items():
            if len(items) <= 1:
                # Unique file size: definitely not a duplicate of anything scanned!
                continue

            for item in items:
                sha = item.get("sha256")
                if not sha:
                    sha = compute_sha256(item["path"])
                    item["sha256"] = sha

                if sha:
                    hash_buckets.setdefault(sha, []).append(item)

                processed += 1
                if progress_callback and candidate_count > 0:
                    progress_callback(processed, candidate_count)

        # Step 3: Format duplicate groups
        duplicate_groups = []
        group_id = 1
        for sha, matched_photos in hash_buckets.items():
            if len(matched_photos) > 1:
                # Sort photos by resolution (width*height) descending, then mtime
                sorted_photos = sorted(
                    matched_photos,
                    key=lambda p: (
                        (p.get("width") or 0) * (p.get("height") or 0),
                        p.get("mtime") or 0
                    ),
                    reverse=True
                )
                
                # Recommend keeping the first one (highest resolution/original)
                primary_item = sorted_photos[0]
                redundant_items = sorted_photos[1:]
                
                recoverable_bytes = sum(p.get("size", 0) for p in redundant_items)

                duplicate_groups.append({
                    "group_id": f"dup_{group_id}",
                    "hash": sha,
                    "file_size": sorted_photos[0].get("size", 0),
                    "photos": sorted_photos,
                    "recommended_keep": primary_item["path"],
                    "suggested_redundant": [p["path"] for p in redundant_items],
                    "recoverable_bytes": recoverable_bytes
                })
                group_id += 1

        return duplicate_groups
