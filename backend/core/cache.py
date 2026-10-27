import os
import json
import hashlib
from typing import Dict, Any, Optional

class MetadataCache:
    """
    Persistent JSON metadata cache.
    Stores extracted hashes, dimensions, embeddings, and face tags.
    Validates cache entries using file modification time (mtime) and file size.
    """

    def __init__(self, cache_dir: str = ".photovault_cache"):
        self.cache_dir = cache_dir
        self.thumbnails_dir = os.path.join(cache_dir, "thumbnails")
        self.cache_file = os.path.join(cache_dir, "metadata_cache.json")
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._dirty = False
        
        self._ensure_dirs()
        self.load()

    def _ensure_dirs(self) -> None:
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)

    def load(self) -> None:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._entries = json.load(f)
            except Exception as e:
                print(f"[Cache] Failed to load cache file, starting fresh: {e}")
                self._entries = {}
        else:
            self._entries = {}

    def save(self) -> None:
        if not self._dirty:
            return
        temp_file = self.cache_file + ".tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, indent=2, ensure_ascii=False)
            if os.path.exists(self.cache_file):
                os.replace(temp_file, self.cache_file)
            else:
                os.rename(temp_file, self.cache_file)
            self._dirty = False
        except Exception as e:
            print(f"[Cache] Failed to save cache: {e}")

    def get_thumbnail_path(self, file_path: str) -> str:
        """Derives a deterministic thumbnail path based on MD5 of file path."""
        path_hash = hashlib.md5(file_path.encode("utf-8")).hexdigest()
        return os.path.join(self.thumbnails_dir, f"{path_hash}.webp")

    def get(self, file_path: str, mtime: float, size: int) -> Optional[Dict[str, Any]]:
        entry = self._entries.get(file_path)
        if not entry:
            return None
        # Invalidate if mtime or size differs
        if entry.get("mtime") != mtime or entry.get("size") != size:
            return None
        return entry

    def put(self, file_path: str, metadata: Dict[str, Any]) -> None:
        self._entries[file_path] = metadata
        self._dirty = True

    def remove(self, file_path: str) -> None:
        if file_path in self._entries:
            del self._entries[file_path]
            self._dirty = True

    def clear(self) -> None:
        self._entries.clear()
        self._dirty = True
        self.save()

    def export_metadata(self, export_path: str) -> None:
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(self._entries, f, indent=2, ensure_ascii=False)

    def import_metadata(self, import_path: str) -> None:
        with open(import_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self._entries.update(data)
            self._dirty = True
            self.save()
