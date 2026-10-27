import pytest
from core.duplicates import ExactDuplicateEngine, compute_sha256

def test_same_size_different_content_are_not_duplicates(tmp_path):
    engine = ExactDuplicateEngine()
    
    # Create two files with exact same byte size (5000 bytes) but different bytes
    file_a = tmp_path / "photo_a.jpg"
    file_b = tmp_path / "photo_b.jpg"

    content_a = b"A" * 5000
    content_b = b"B" * 5000

    file_a.write_bytes(content_a)
    file_b.write_bytes(content_b)

    assert file_a.stat().st_size == file_b.stat().st_size == 5000
    assert compute_sha256(str(file_a)) != compute_sha256(str(file_b))

    photos = [
        {"path": str(file_a), "size": 5000, "width": 100, "height": 100},
        {"path": str(file_b), "size": 5000, "width": 100, "height": 100}
    ]

    duplicates = engine.find_duplicates(photos)
    assert len(duplicates) == 0, "Files with identical size but different contents must NOT be duplicates!"

def test_true_duplicates_are_detected(tmp_path):
    engine = ExactDuplicateEngine()
    
    file_1 = tmp_path / "original.jpg"
    file_2 = tmp_path / "copy.jpg"

    data = b"REAL_IMAGE_BYTES_1234567890" * 200
    file_1.write_bytes(data)
    file_2.write_bytes(data)

    photos = [
        {"path": str(file_1), "size": len(data), "width": 200, "height": 200, "mtime": 1000},
        {"path": str(file_2), "size": len(data), "width": 200, "height": 200, "mtime": 2000}
    ]

    duplicates = engine.find_duplicates(photos)
    assert len(duplicates) == 1
    group = duplicates[0]
    assert len(group["photos"]) == 2
    assert group["recommended_keep"] in [str(file_1), str(file_2)]
