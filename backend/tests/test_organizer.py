import pytest
from core.organizer import SafeOrganizer

def test_dry_run_plan_generation(tmp_path):
    organizer = SafeOrganizer()
    target_dir = tmp_path / "Organized"
    
    photos = [
        {"path": "D:/photo1.jpg", "filename": "photo1.jpg", "tags": ["Nature"], "size": 1024},
        {"path": "D:/photo2.jpg", "filename": "photo2.jpg", "tags": ["Food"], "size": 2048}
    ]

    plan = organizer.generate_plan(
        photos=photos,
        target_root=str(target_dir),
        group_by="category",
        action="copy"
    )

    assert len(plan) == 2
    assert "Nature" in plan[0]["destination"]
    assert "Food" in plan[1]["destination"]
    assert plan[0]["action"] == "copy"
    # Ensure no files were created during dry-run
    assert not target_dir.exists()
