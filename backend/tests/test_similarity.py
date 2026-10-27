import pytest
from core.similarity import VisualSimilarityEngine

def test_visual_similarity_hamming_and_thresholds():
    engine = VisualSimilarityEngine()
    
    # Identical hashes
    dist_zero = engine.compute_hamming_distance("ffffffffffffffff", "ffffffffffffffff")
    assert dist_zero == 0

    # 1 bit difference
    dist_one = engine.compute_hamming_distance("fffffffffffffffe", "ffffffffffffffff")
    assert dist_one == 1

    # Completely different
    dist_high = engine.compute_hamming_distance("0000000000000000", "ffffffffffffffff")
    assert dist_high == 64

def test_similar_groups_clustering():
    engine = VisualSimilarityEngine()
    photos = [
        {"path": "p1.jpg", "phash": "ffffffffffffff00", "dhash": "ffffffffffffff00", "width": 1000, "height": 1000},
        {"path": "p2.jpg", "phash": "ffffffffffffff01", "dhash": "ffffffffffffff01", "width": 800, "height": 800},
        {"path": "p3.jpg", "phash": "0000000000000000", "dhash": "0000000000000000", "width": 500, "height": 500}
    ]

    groups = engine.find_similar_groups(photos, mode="strict")
    assert len(groups) == 1
    assert groups[0]["count"] == 2
    assert "p1.jpg" in [p["path"] for p in groups[0]["photos"]]
    assert "p2.jpg" in [p["path"] for p in groups[0]["photos"]]
