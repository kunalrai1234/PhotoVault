import os
import sys
import json
import socket
import argparse
import threading
import time
from typing import Dict, Any, List, Optional
from wsgiref.simple_server import WSGIServer, make_server
from socketserver import ThreadingMixIn
from bottle import Bottle, request, response, static_file, run, ServerAdapter

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from core.utils import get_resource_path, find_available_port
from core.cache import MetadataCache
from core.scanner import FolderScanner, sanitize_folder_path
from core.duplicates import ExactDuplicateEngine
from core.similarity import VisualSimilarityEngine
from core.faces import FaceEngine
from core.categories import LocalCategorizer
from core.organizer import SafeOrganizer
from core.security import CredentialVault
from adapters.gemini_adapter import GeminiAdapter
from adapters.openai_adapter import OpenAIAdapter
from adapters.claude_adapter import ClaudeAdapter

# Initialize singletons with robust path resolution
cache = MetadataCache()
scanner = FolderScanner(cache=cache)
duplicate_engine = ExactDuplicateEngine()
similarity_engine = VisualSimilarityEngine()
models_path = get_resource_path("assets/models")
face_engine = FaceEngine(models_dir=models_path)
categorizer = LocalCategorizer()
organizer = SafeOrganizer()

# App State
state: Dict[str, Any] = {
    "scanned_folders": [],
    "photos": [],
    "duplicate_groups": [],
    "similarity_groups": [],
    "face_clusters": [],
    "scan_progress": {
        "current": 0,
        "total": 0,
        "status": "idle",
        "active": False,
        "phase": "idle"
    },
    "ai_settings": {
        "gemini": {"enabled": False, "model": "gemini-3.5-flash"},
        "openai": {"enabled": False, "model": "gpt-4o", "base_url": "https://api.openai.com/v1"},
        "claude": {"enabled": False, "model": "claude-3-5-sonnet-20241022"}
    }
}

# Scan background lock
scan_lock = threading.Lock()

# Multi-threaded WSGI Server for Bottle
class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True
    request_queue_size = 64

class ThreadedServer(ServerAdapter):
    server_instance: Optional[WSGIServer] = None

    def run(self, handler):
        self.server_instance = make_server(self.host, self.port, handler, server_class=ThreadedWSGIServer)
        self.server_instance.serve_forever()

    def shutdown(self):
        if self.server_instance:
            self.server_instance.shutdown()

app = Bottle()

def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With'

@app.hook('after_request')
def after_request():
    enable_cors()

@app.route('/api/<:re:.*>', method='OPTIONS')
def handle_options():
    return {}

# 1. Native Windows Folder Picker Dialog
@app.route('/api/pick-folder', method='POST')
def pick_folder():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder = filedialog.askdirectory(title="Select Photo Folder to Scan with PhotoVault")
        root.destroy()
        if folder:
            sanitized = sanitize_folder_path(folder)
            return {"folder": sanitized}
        return {"folder": None}
    except Exception as e:
        print(f"[PickFolder] Dialog error: {e}")
        return {"folder": None, "error": str(e)}

# 2. Status & Dashboard
@app.route('/api/status', method='GET')
def get_status():
    return {
        "status": "online",
        "total_photos": len(state["photos"]),
        "duplicate_groups_count": len(state["duplicate_groups"]),
        "similarity_groups_count": len(state["similarity_groups"]),
        "face_clusters_count": len(state["face_clusters"]),
        "scan_progress": state["scan_progress"]
    }

# 3. Asynchronous Folder Scanning Engine
def _run_scan_thread(folders: List[str]):
    with scan_lock:
        state["scan_progress"]["active"] = True
        state["scan_progress"]["phase"] = "scanning"
        state["scan_progress"]["current"] = 0
        state["scan_progress"]["total"] = 0
        state["scan_progress"]["status"] = "Discovering photos..."

        def on_progress(current: int, path: str):
            state["scan_progress"]["current"] = current
            state["scan_progress"]["status"] = f"Reading {os.path.basename(path)}"

        try:
            # 1. Recursive scan & thumbnail extraction
            photos = scanner.scan_paths(folders, progress_callback=on_progress)
            total_photos = len(photos)
            state["scan_progress"]["total"] = total_photos

            if scanner.is_cancelled:
                state["scan_progress"]["status"] = "Scan cancelled"
                state["scan_progress"]["active"] = False
                state["scan_progress"]["phase"] = "cancelled"
                return

            # 2. Extract faces and categories
            state["scan_progress"]["phase"] = "analyzing"
            for idx, photo in enumerate(photos):
                if scanner.is_cancelled:
                    break
                state["scan_progress"]["status"] = f"Analyzing faces & visual features ({idx + 1}/{total_photos})"
                state["scan_progress"]["current"] = idx + 1
                try:
                    faces = face_engine.detect_faces(photo["path"])
                    photo["faces"] = faces
                    photo["tags"] = categorizer.categorize_image(photo, faces=faces)
                    cache.put(photo["path"], photo)
                except Exception as e:
                    print(f"[Scan] Error analyzing {photo['path']}: {e}")

            if scanner.is_cancelled:
                state["scan_progress"]["status"] = "Scan cancelled"
                state["scan_progress"]["active"] = False
                state["scan_progress"]["phase"] = "cancelled"
                return

            cache.save()
            state["photos"] = photos

            # 3. Exact duplicates
            state["scan_progress"]["status"] = "Detecting duplicate groups..."
            state["duplicate_groups"] = duplicate_engine.find_duplicates(photos)

            # 4. Visual similarity
            state["scan_progress"]["status"] = "Clustering visually similar & burst photos..."
            state["similarity_groups"] = similarity_engine.find_similar_groups(photos, mode="balanced")

            # 5. Face clusters
            state["scan_progress"]["status"] = "Clustering person albums..."
            state["face_clusters"] = face_engine.cluster_faces()

            state["scan_progress"] = {
                "current": total_photos,
                "total": total_photos,
                "status": f"Scan completed ({total_photos} photos indexed)",
                "active": False,
                "phase": "completed"
            }

        except Exception as e:
            print(f"[Scan] Fatal error during scan: {e}")
            state["scan_progress"] = {
                "current": 0,
                "total": 0,
                "status": f"Scan error: {e}",
                "active": False,
                "phase": "error"
            }

@app.route('/api/scan', method='POST')
def start_scan():
    if state["scan_progress"]["active"]:
        return {"status": "busy", "message": "A scan is already in progress"}

    data = request.json or {}
    raw_folders = data.get("folders", [])
    if not raw_folders:
        response.status = 400
        return {"error": "No folders specified."}

    # Clean and filter folder paths
    folders = []
    for f in raw_folders:
        clean = sanitize_folder_path(f)
        if clean and os.path.exists(clean) and clean not in folders:
            folders.append(clean)

    if not folders:
        response.status = 400
        return {"error": "None of the specified folders exist on this computer."}

    state["scanned_folders"] = folders
    scanner.is_cancelled = False

    # Launch in non-blocking background thread
    worker = threading.Thread(target=_run_scan_thread, args=(folders,), daemon=True)
    worker.start()

    return {
        "status": "started",
        "message": f"Scan started for {len(folders)} folder(s)"
    }

@app.route('/api/scan/cancel', method='POST')
def cancel_scan():
    scanner.cancel()
    state["scan_progress"]["status"] = "Cancelling scan..."
    state["scan_progress"]["active"] = False
    state["scan_progress"]["phase"] = "cancelled"
    return {"status": "cancelled"}

# 4. Photos List & Filtering
@app.route('/api/photos', method='GET')
def get_photos():
    category = request.query.get('category')
    search = request.query.get('search', '').lower()

    filtered = state["photos"]
    if category and category != "All":
        filtered = [p for p in filtered if category in (p.get("tags") or [])]
    if search:
        filtered = [p for p in filtered if search in p.get("filename", "").lower()]

    return {"photos": filtered, "total": len(filtered)}

# 5. Duplicates API
@app.route('/api/duplicates', method='GET')
def get_duplicates():
    return {"groups": state["duplicate_groups"]}

# 6. Visual Similarity API
@app.route('/api/similarity', method='GET')
def get_similarity():
    mode = request.query.get('mode', 'balanced')
    if mode in ["strict", "balanced", "loose"]:
        state["similarity_groups"] = similarity_engine.find_similar_groups(state["photos"], mode=mode)
    return {"groups": state["similarity_groups"], "mode": mode}

# 7. Face Clusters API
@app.route('/api/faces', method='GET')
def get_faces():
    return {"clusters": state["face_clusters"]}

@app.route('/api/faces/rename', method='POST')
def rename_face_cluster():
    data = request.json or {}
    cid = data.get("cluster_id")
    new_name = data.get("name")
    if cid and new_name:
        success = face_engine.rename_cluster(cid, new_name)
        if success:
            state["face_clusters"] = list(face_engine.clusters.values())
            return {"success": True}
    response.status = 400
    return {"error": "Invalid cluster_id or name"}

@app.route('/api/faces/merge', method='POST')
def merge_face_clusters():
    data = request.json or {}
    tgt = data.get("target_id")
    src = data.get("source_id")
    if tgt and src:
        success = face_engine.merge_clusters(tgt, src)
        if success:
            state["face_clusters"] = list(face_engine.clusters.values())
            return {"success": True}
    response.status = 400
    return {"error": "Invalid target or source id"}

# 8. Safe Cleanup & Recycle Bin API
@app.route('/api/cleanup/recycle', method='POST')
def recycle_files():
    data = request.json or {}
    file_paths = data.get("files", [])
    if not file_paths:
        response.status = 400
        return {"error": "No files selected."}

    result = organizer.safe_delete_files(file_paths)
    recycled_set = set(result.get("recycled_files", []))
    state["photos"] = [p for p in state["photos"] if p["path"] not in recycled_set]
    
    state["duplicate_groups"] = duplicate_engine.find_duplicates(state["photos"])
    state["similarity_groups"] = similarity_engine.find_similar_groups(state["photos"])

    return result

# 9. Organization Plan & Execution API
@app.route('/api/organize/plan', method='POST')
def plan_organization():
    data = request.json or {}
    target_root = data.get("target_root")
    group_by = data.get("group_by", "category")
    action = data.get("action", "copy")

    if not target_root:
        response.status = 400
        return {"error": "Target directory is required."}

    clean_target = sanitize_folder_path(target_root)
    plan = organizer.generate_plan(
        photos=state["photos"],
        target_root=clean_target,
        group_by=group_by,
        action=action
    )
    return {"plan": plan, "total_actions": len(plan)}

@app.route('/api/organize/execute', method='POST')
def execute_organization():
    data = request.json or {}
    plan = data.get("plan", [])
    if not plan:
        response.status = 400
        return {"error": "Empty plan."}

    result = organizer.execute_plan(plan)
    return result

# 10. AI Vision Description & Tagging API
@app.route('/api/ai/describe', method='POST')
def ai_describe_photo():
    data = request.json or {}
    image_path = data.get("image_path")
    prompt = data.get("prompt", "Analyze this photo in 2-3 sentences. Identify what is in the scene, the setting, subjects, and main colors.")

    if not image_path or not os.path.exists(image_path):
        response.status = 400
        return {"error": "Image file not found."}

    key = CredentialVault.get_api_key("gemini")
    if not key:
        response.status = 400
        return {"error": "Gemini API key is not configured in Settings."}

    adapter = GeminiAdapter(api_key=key, model_name=state["ai_settings"]["gemini"]["model"], is_enabled=True)
    res = adapter.analyze_images([image_path], prompt=prompt)
    return res

# 11. AI Settings & Secure Key Storage API
@app.route('/api/ai/settings', method='GET')
def get_ai_settings():
    providers = {}
    for prov in ["gemini", "openai", "claude"]:
        key = CredentialVault.get_api_key(prov)
        providers[prov] = {
            **state["ai_settings"][prov],
            "has_key": bool(key),
            "masked_key": CredentialVault.mask_key(key) if key else ""
        }
    return {"providers": providers}

@app.route('/api/ai/save-key', method='POST')
def save_ai_key():
    data = request.json or {}
    provider = data.get("provider")
    key = data.get("api_key")
    enabled = data.get("enabled", True)

    if provider in ["gemini", "openai", "claude"]:
        if key:
            CredentialVault.set_api_key(provider, key)
        state["ai_settings"][provider]["enabled"] = enabled
        return {"success": True}
    response.status = 400
    return {"error": "Invalid provider."}

@app.route('/api/ai/test-connection', method='POST')
def test_ai_connection():
    data = request.json or {}
    provider = data.get("provider", "gemini")
    key = CredentialVault.get_api_key(provider)
    if not key:
        return {"success": False, "message": "No API key found in Windows Credential Manager."}

    if provider == "gemini":
        adapter = GeminiAdapter(api_key=key, model_name=state["ai_settings"]["gemini"]["model"])
    elif provider == "openai":
        adapter = OpenAIAdapter(api_key=key, model_name=state["ai_settings"]["openai"]["model"])
    elif provider == "claude":
        adapter = ClaudeAdapter(api_key=key, model_name=state["ai_settings"]["claude"]["model"])
    else:
        return {"success": False, "message": "Unsupported provider."}

    return adapter.test_connection()

# 12. Thumbnail & Local File Serving
@app.route('/thumbnail/<path:path>')
def serve_thumbnail(path):
    return static_file(path, root=cache.thumbnails_dir)

@app.route('/local-image/<path:path>')
def serve_local_image(path):
    if ":" in path:
        drive, rest = path.split(":", 1)
        full_path = drive + ":" + rest
        root_dir = os.path.dirname(full_path)
        fname = os.path.basename(full_path)
        return static_file(fname, root=root_dir)
    return static_file(path, root="/")

# Static frontend serving
@app.route('/')
@app.route('/<path:path>')
def serve_frontend(path="index.html"):
    dist_dir = get_resource_path("dist")
    if os.path.exists(os.path.join(dist_dir, path)):
        return static_file(path, root=dist_dir)
    src_dir = get_resource_path("src")
    if os.path.exists(os.path.join(src_dir, path)):
        return static_file(path, root=src_dir)
    assets_dir = get_resource_path("assets")
    if path.startswith("assets/") and os.path.exists(os.path.join(assets_dir, path.replace("assets/", "", 1))):
        return static_file(path.replace("assets/", "", 1), root=assets_dir)
    return static_file("index.html", root=dist_dir if os.path.exists(dist_dir) else src_dir)

def run_desktop_app(port: Optional[int] = None):
    import webview

    active_port = port if port else find_available_port(54321)
    server_adapter = ThreadedServer(host="127.0.0.1", port=active_port)

    server_thread = threading.Thread(
        target=lambda: run(app, server=server_adapter, quiet=True),
        daemon=True
    )
    server_thread.start()

    # Small delay for socket listener to attach
    time.sleep(0.3)

    class DesktopAPI:
        def select_folder(self):
            try:
                window = webview.windows[0]
                result = window.create_file_dialog(webview.FOLDER_DIALOG)
                if result and len(result) > 0:
                    return result[0]
            except Exception:
                pass
            return None

    api = DesktopAPI()
    icon_path = get_resource_path("assets/icon.ico")
    if not os.path.exists(icon_path):
        icon_path = None

    try:
        window = webview.create_window(
            title="PhotoVault Local AI",
            url=f"http://127.0.0.1:{active_port}",
            width=1280,
            height=820,
            min_size=(1024, 700),
            js_api=api
        )

        def on_closed():
            # Ensure clean exit and no orphaned threads or processes
            try:
                server_adapter.shutdown()
            except Exception:
                pass
            os._exit(0)

        window.events.closed += on_closed
        webview.start(debug=False)
    except Exception as e:
        print(f"[PhotoVault] Desktop GUI failed to launch: {e}")
        import webbrowser
        webbrowser.open(f"http://127.0.0.1:{active_port}")
        while True:
            time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PhotoVault Local AI")
    parser.add_argument("--desktop", action="store_true", help="Launch native desktop window")
    parser.add_argument("--server", action="store_true", help="Launch headless API server only")
    parser.add_argument("--port", type=int, default=None, help="Server port (auto-allocated if omitted)")
    args = parser.parse_args()

    # If --server is explicitly requested, run headless server
    # Otherwise (e.g. double-click in explorer, desktop shortcut), default to native GUI
    if args.server:
        launch_gui = False
    else:
        launch_gui = True

    if launch_gui:
        run_desktop_app(port=args.port)
    else:
        active_port = args.port if args.port else find_available_port(54321)
        print(f"[PhotoVault] Starting local multi-threaded API server at http://127.0.0.1:{active_port}...")
        run(app, server=ThreadedServer, host="127.0.0.1", port=active_port, reloader=False)
