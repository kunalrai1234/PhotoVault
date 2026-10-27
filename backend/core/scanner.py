import os
import time
from typing import List, Dict, Any, Generator, Callable, Optional
from PIL import Image, ImageOps
import imagehash
from .cache import MetadataCache

# Supported image file extensions
SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".tif"
}

class FolderScanner:
    """
    Recursively scans directories for supported images without depth limits.
    Resilient to corrupt files, extracts metadata, perceptual hashes, and thumbnails.
    """

    def __init__(self, cache: MetadataCache):
        self.cache = cache
        self.is_cancelled = False

    def cancel(self) -> None:
        self.is_cancelled = True

    def scan_paths(
        self,
        root_folders: List[str],
        progress_callback: Optional[Callable[[int, str], None]] = None,
        extract_phash: bool = True
    ) -> List[Dict[str, Any]]:
        self.is_cancelled = False
        all_photos: List[Dict[str, Any]] = []
        count = 0

        # First pass: gather file candidates rapidly
        file_candidates: List[tuple[str, str]] = [] # (root, full_path)
        for root_dir in root_folders:
            if not os.path.exists(root_dir):
                continue
            for dirpath, _, filenames in os.walk(root_dir):
                if self.is_cancelled:
                    break
                for fname in filenames:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        full_path = os.path.join(dirpath, fname)
                        file_candidates.append((root_dir, full_path))

        total_files = len(file_candidates)
        print(f"[Scanner] Found {total_files} potential image files to process.")

        # Second pass: extract metadata with cache check
        for root_dir, file_path in file_candidates:
            if self.is_cancelled:
                print("[Scanner] Scan cancelled by user.")
                break

            count += 1
            if progress_callback:
                progress_callback(count, file_path)

            photo_meta = self.process_image_file(root_dir, file_path, extract_phash=extract_phash)
            if photo_meta:
                all_photos.append(photo_meta)

        self.cache.save()
        return all_photos

    def process_image_file(
        self,
        root_dir: str,
        file_path: str,
        extract_phash: bool = True
    ) -> Optional[Dict[str, Any]]:
        try:
            stat = os.stat(file_path)
            file_size = stat.st_size
            mtime = stat.st_mtime

            # Check cache first
            cached = self.cache.get(file_path, mtime, file_size)
            thumbnail_path = self.cache.get_thumbnail_path(file_path)
            has_thumbnail = os.path.exists(thumbnail_path)

            if cached and has_thumbnail:
                return cached

            # Extract basic file attributes
            fname = os.path.basename(file_path)
            ext = os.path.splitext(fname)[1].lower()
            rel_path = os.path.relpath(file_path, root_dir)

            width = 0
            height = 0
            fmt = ext.replace(".", "").upper()
            phash_str = cached.get("phash", "") if cached else ""
            dhash_str = cached.get("dhash", "") if cached else ""
            is_corrupt = False

            try:
                with Image.open(file_path) as img:
                    # Auto-orient based on EXIF tag
                    try:
                        img = ImageOps.exif_transpose(img)
                    except Exception:
                        pass

                    width, height = img.size
                    fmt = (img.format or fmt).upper()

                    # Generate thumbnail if missing
                    if not has_thumbnail:
                        thumb = img.copy()
                        thumb.thumbnail((256, 256), Image.Resampling.LANCZOS)
                        if thumb.mode in ("RGBA", "LA", "P"):
                            # Convert to RGB with white background if saving webp/jpeg
                            background = Image.new("RGB", thumb.size, (255, 255, 255))
                            background.paste(thumb, mask=thumb.split()[-1] if thumb.mode == "RGBA" else None)
                            thumb = background
                        elif thumb.mode != "RGB":
                            thumb = thumb.convert("RGB")
                        thumb.save(thumbnail_path, "WEBP", quality=80)

                    # Perceptual hashes
                    if extract_phash and (not phash_str or not dhash_str):
                        phash_val = imagehash.phash(img)
                        dhash_val = imagehash.dhash(img)
                        phash_str = str(phash_val)
                        dhash_str = str(dhash_val)

            except Exception as img_err:
                # Corrupted or unreadable image file
                is_corrupt = True
                print(f"[Scanner] Unreadable image '{file_path}': {img_err}")

            metadata: Dict[str, Any] = {
                "id": self.cache.get_thumbnail_path(file_path).split(os.sep)[-1].replace(".webp", ""),
                "filename": fname,
                "path": file_path,
                "relative_path": rel_path,
                "root_dir": root_dir,
                "extension": ext,
                "size": file_size,
                "mtime": mtime,
                "date_modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime)),
                "width": width,
                "height": height,
                "format": fmt,
                "sha256": cached.get("sha256", "") if cached else "",
                "phash": phash_str,
                "dhash": dhash_str,
                "thumbnail": thumbnail_path,
                "is_corrupt": is_corrupt,
                "faces": cached.get("faces", []) if cached else [],
                "tags": cached.get("tags", []) if cached else []
            }

            self.cache.put(file_path, metadata)
            return metadata

        except Exception as e:
            print(f"[Scanner] File access error on '{file_path}': {e}")
            return None
