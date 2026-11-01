import os
import pytest
import numpy as np
from core.faces import FaceEngine

def test_face_engine_initialization_and_clustering():
    engine = FaceEngine()
    assert os.path.exists(engine.models_dir)
    assert os.path.exists(engine.yunet_path)
    assert os.path.exists(engine.sface_path)

    # Test clustering with dummy embeddings
    # 2 faces of Person A (close vectors), 1 face of Person B (distant)
    emb_a1 = [1.0] + [0.0] * 127
    emb_a2 = [0.99] + [0.01] * 127
    emb_b = [0.0] * 64 + [1.0] + [0.0] * 63

    engine.face_metadata = {
        "f1": {"face_id": "f1", "image_path": "photo1.jpg", "box": [10, 10, 50, 50], "embedding": emb_a1},
        "f2": {"face_id": "f2", "image_path": "photo2.jpg", "box": [20, 20, 50, 50], "embedding": emb_a2},
        "f3": {"face_id": "f3", "image_path": "photo3.jpg", "box": [30, 30, 50, 50], "embedding": emb_b},
    }

    clusters = engine.cluster_faces(threshold=0.363)
    assert len(clusters) == 2
    # Cluster 1: Person 01 with 2 photos
    # Cluster 2: Unknown / Unmatched with 1 photo
    named_clusters = [c for c in clusters if c["cluster_id"].startswith("person_0")]
    unknown_clusters = [c for c in clusters if c["cluster_id"] == "person_unknown"]
    
    assert len(named_clusters) == 1
    assert named_clusters[0]["photo_count"] == 2
    assert len(unknown_clusters) == 1
    assert unknown_clusters[0]["photo_count"] == 1

    # Test renaming cluster
    assert engine.rename_cluster("person_01", "Alice")
    assert engine.clusters["person_01"]["name"] == "Alice"
