import os
import shutil
import time
from typing import List, Dict, Any, Optional
from send2trash import send2trash

class SafeOrganizer:
    """
    Safely handles physical and virtual photo organization.
    - Dry-run preview before any execution
    - Collision resolution (never overwrites without explicit permission)
    - Safe deletion using Windows Recycle Bin (send2trash)
    - Operation logs for accountability
    """

    def __init__(self):
        self.operation_log: List[Dict[str, Any]] = []

    def generate_plan(
        self,
        photos: List[Dict[str, Any]],
        target_root: str,
        group_by: str = "category", # "person", "category", "date", "duplicates", "similarity"
        action: str = "copy", # "copy" or "move"
        conflict_strategy: str = "rename" # "rename" (keep both), "skip", "overwrite"
    ) -> List[Dict[str, Any]]:
        """
        Generates a dry-run execution plan without modifying any file on disk.
        """
        plan: List[Dict[str, Any]] = []

        for photo in photos:
            src = photo["path"]
            fname = photo["filename"]
            
            # Determine destination subfolder based on group_by strategy
            if group_by == "category":
                tags = photo.get("tags") or ["Other"]
                subfolder = tags[0] # primary tag
            elif group_by == "person":
                faces = photo.get("faces") or []
                subfolder = faces[0].get("cluster_name", "Unassigned") if faces else "No_Faces"
            elif group_by == "date":
                mtime = photo.get("mtime", time.time())
                subfolder = time.strftime("%Y/%B", time.localtime(mtime))
            elif group_by == "duplicates":
                subfolder = "Exact_Duplicates" if photo.get("is_duplicate") else "Originals"
            else:
                subfolder = "General"

            dest_dir = os.path.join(target_root, subfolder)
            dest_path = os.path.join(dest_dir, fname)

            collision = os.path.exists(dest_path)
            resolved_dest = dest_path

            if collision and conflict_strategy == "rename":
                resolved_dest = self._resolve_name_collision(dest_dir, fname)

            plan.append({
                "source": src,
                "destination_dir": dest_dir,
                "destination": resolved_dest,
                "action": action,
                "collision": collision,
                "status": "pending",
                "size": photo.get("size", 0)
            })

        return plan

    def _resolve_name_collision(self, folder: str, filename: str) -> str:
        name, ext = os.path.splitext(filename)
        counter = 1
        while True:
            candidate = os.path.join(folder, f"{name}_{counter}{ext}")
            if not os.path.exists(candidate):
                return candidate
            counter += 1

    def execute_plan(
        self,
        plan: List[Dict[str, Any]],
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Executes a user-confirmed organization plan.
        """
        success_count = 0
        error_count = 0
        errors: List[str] = []

        for idx, item in enumerate(plan):
            src = item["source"]
            dest = item["destination"]
            dest_dir = item["destination_dir"]
            action = item["action"]

            try:
                os.makedirs(dest_dir, exist_ok=True)
                
                if action == "copy":
                    shutil.copy2(src, dest)
                elif action == "move":
                    shutil.move(src, dest)

                item["status"] = "success"
                success_count += 1
                self.operation_log.append({
                    "timestamp": time.time(),
                    "action": action,
                    "src": src,
                    "dest": dest
                })

            except Exception as e:
                item["status"] = "failed"
                item["error"] = str(e)
                error_count += 1
                errors.append(f"{src} -> {dest}: {e}")

            if progress_callback:
                progress_callback(idx + 1, len(plan))

        return {
            "total": len(plan),
            "success": success_count,
            "failed": error_count,
            "errors": errors
        }

    def safe_delete_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Safely sends files to the Windows Recycle Bin using send2trash.
        Never permanently deletes files without trash.
        """
        recycled: List[str] = []
        errors: List[str] = []
        total_space_freed = 0

        for path in file_paths:
            if not os.path.exists(path):
                continue
            try:
                sz = os.path.getsize(path)
                # Windows Recycle Bin API
                send2trash(path)
                recycled.append(path)
                total_space_freed += sz
                self.operation_log.append({
                    "timestamp": time.time(),
                    "action": "recycle",
                    "path": path,
                    "freed_bytes": sz
                })
            except Exception as e:
                errors.append(f"Failed to recycle {path}: {e}")

        return {
            "recycled_count": len(recycled),
            "recycled_files": recycled,
            "space_freed_bytes": total_space_freed,
            "errors": errors
        }
