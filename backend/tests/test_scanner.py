import os
import shutil
import pytest
from PIL import Image
from core.cache import MetadataCache
from core.scanner import FolderScanner

@pytest.fixture
def temp_scanner_env(tmp_path):
    test_dir = tmp_path / "photos"
    test_dir.mkdir()
    
    # Create 5 nested levels
    nested = test_dir / "lvl1" / "lvl2" / "lvl3" / "lvl4" / "lvl5"
    nested.mkdir(parents=True)
    
    # Create valid images
    img1_path = test_dir / "photo1.jpg"
    img2_path = nested / "deep_photo.png"
    
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(str(img1_path))
    img.save(str(img2_path))

    # Create a corrupted file
    corrupt_path = test_dir / "corrupted.jpg"
    with open(str(corrupt_path), "wb") as f:
        f.write(b"NOT_AN_IMAGE_DATA_CORRUPTED")

    cache_dir = tmp_path / "cache"
    cache = MetadataCache(cache_dir=str(cache_dir))
    scanner = FolderScanner(cache=cache)

    yield {
        "root": str(test_dir),
        "scanner": scanner,
        "valid_paths": [str(img1_path), str(img2_path)],
        "corrupt_path": str(corrupt_path)
    }

def test_recursive_scanner_and_corruption_resilience(temp_scanner_env):
    scanner = temp_scanner_env["scanner"]
    root = temp_scanner_env["root"]
    
    results = scanner.scan_paths([root])
    assert len(results) >= 2
    
    # Ensure deep nested file was discovered
    paths = [r["path"] for r in results]
    assert temp_scanner_env["valid_paths"][1] in paths
    
    # Check corrupt file was handled gracefully without crash
    corrupt_entries = [r for r in results if r["path"] == temp_scanner_env["corrupt_path"]]
    if corrupt_entries:
        assert corrupt_entries[0]["is_corrupt"] is True
