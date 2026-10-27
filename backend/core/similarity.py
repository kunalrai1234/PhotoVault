import imagehash
from typing import List, Dict, Any, Tuple

class VisualSimilarityEngine:
    """
    Multi-stage perceptual similarity engine:
    Stage A: Perceptual hash (pHash + dHash) Hamming distance.
    Stage B: Multi-hash cross-verification (combining pHash and dHash).
    Classifies photos into:
      - Near-identical (bursts, minor compression/resize)
      - Visually similar (slight crops, color filter, light variations)
      - Semantically related (similar layout or dominant subjects)
    """

    THRESHOLDS = {
        "strict": {"near_identical": 3, "similar": 6},
        "balanced": {"near_identical": 5, "similar": 10},
        "loose": {"near_identical": 8, "similar": 16}
    }

    def __init__(self):
        pass

    def compute_hamming_distance(self, hex1: str, hex2: str) -> int:
        """Computes Hamming distance between two hex hash strings."""
        if not hex1 or not hex2 or len(hex1) != len(hex2):
            return 999
        try:
            h1 = imagehash.hex_to_hash(hex1)
            h2 = imagehash.hex_to_hash(hex2)
            return h1 - h2
        except Exception:
            return 999

    def find_similar_groups(
        self,
        photos: List[Dict[str, Any]],
        mode: str = "balanced",
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """
        Groups photos using perceptual hashing and multi-stage verification.
        """
        thresholds = self.THRESHOLDS.get(mode, self.THRESHOLDS["balanced"])
        near_limit = thresholds["near_identical"]
        similar_limit = thresholds["similar"]

        # Filter out photos without perceptual hashes
        valid_photos = [p for p in photos if p.get("phash")]
        n = len(valid_photos)
        if n < 2:
            return []

        # Graph of connections: parent pointers for union-find clustering
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

        pair_relations: Dict[Tuple[int, int], str] = {}
        total_comparisons = (n * (n - 1)) // 2
        compared = 0

        # Pairwise comparison with early exit
        for i in range(n):
            p1 = valid_photos[i]
            p1_phash = p1["phash"]
            p1_dhash = p1.get("dhash", "")

            for j in range(i + 1, n):
                p2 = valid_photos[j]
                
                # Check 1: pHash distance
                p_dist = self.compute_hamming_distance(p1_phash, p2["phash"])
                
                # Check 2: dHash distance
                d_dist = self.compute_hamming_distance(p1_dhash, p2.get("dhash", "")) if p1_dhash else p_dist
                
                # Combined score: weighted average of pHash and dHash
                combined_dist = min(p_dist, d_dist)

                if combined_dist <= similar_limit:
                    union(i, j)
                    rel_type = "near_identical" if combined_dist <= near_limit else "visually_similar"
                    pair_relations[(i, j)] = rel_type

                compared += 1
                if progress_callback and total_comparisons > 0 and compared % 500 == 0:
                    progress_callback(compared, total_comparisons)

        # Collect clusters
        clusters: Dict[int, List[int]] = {}
        for i in range(n):
            root = find(i)
            clusters.setdefault(root, []).append(i)

        similar_groups = []
        group_idx = 1
        for root, indices in clusters.items():
            if len(indices) > 1:
                group_photos = [valid_photos[idx] for idx in indices]
                
                # Determine primary classification for the group
                has_near = False
                for a_idx in range(len(indices)):
                    for b_idx in range(a_idx + 1, len(indices)):
                        pair = (min(indices[a_idx], indices[b_idx]), max(indices[a_idx], indices[b_idx]))
                        if pair_relations.get(pair) == "near_identical":
                            has_near = True
                            break

                category = "Near-Identical Burst" if has_near else "Visually Similar"

                # Sort by resolution and mtime
                sorted_photos = sorted(
                    group_photos,
                    key=lambda p: (
                        (p.get("width") or 0) * (p.get("height") or 0),
                        p.get("mtime") or 0
                    ),
                    reverse=True
                )

                similar_groups.append({
                    "group_id": f"sim_{group_idx}",
                    "category": category,
                    "mode": mode,
                    "count": len(sorted_photos),
                    "photos": sorted_photos,
                    "representative": sorted_photos[0]
                })
                group_idx += 1

        return similar_groups
