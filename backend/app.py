import os
import sys
import json
import argparse
from typing import Dict, Any, List
from bottle import Bottle, request, response, static_file, run

# Import local core modules
from core.cache import MetadataCache
from core.scanner import FolderScanner
from core.duplicates import ExactDuplicateEngine
from core.similarity import VisualSimilarityEngine
from core.faces import FaceEngine
from core.categories import LocalCategorizer
from core.organizer import SafeOrganizer
from core.security import CredentialVault
from adapters.gemini_adapter import GeminiAdapter
from adapters.openai_adapter import OpenAIAdapter
from adapters.claude_adapter import ClaudeAdapter

# Initialize singletons
cache = MetadataCache(cache_dir=".photovault_cache")
scanner = FolderScanner(cache=cache)
duplicate_engine = ExactDuplicateEngine()
similarity_engine = VisualSimilarityEngine()
face_engine = FaceEngine(models_dir="assets/models")
categorizer = LocalCategorizer()
organizer = SafeOrganizer()

# App State
state: Dict[str, Any] = {
    "scanned_folders": [],
    "photos": [],
    "duplicate_groups": [],
    "similarity_groups": [],
    "face_clusters": [],
    "scan_progress": {"current": 0, "total": 0, "status": "idle"},
    "ai_settings": {
        "gemini": {"enabled": False, "model": "gemini-1.5-flash"},
        "openai": {"enabled": False, "model": "gpt-4o", "base_url": "https://api.openai.com/v1"},
        "claude": {"enabled": False, "model": "claude-3-5-sonnet-20241022"}
    }
}

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

# 1. Status & Dashboard
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

# 2. Folder Selection & Scanning
@app.route('/api/scan', method='POST')
def start_scan():
    data = request.json or {}
    folders = data.get("folders", [])
    if not folders:
        response.status = 400
        return {"error": "No folders specified."}

    state["scanned_folders"] = folders
    state["scan_progress"] = {"current": 0, "total": 0, "status": "scanning"}

    def on_progress(current: int, path: str):
        state["scan_progress"]["current"] = current
        state["scan_progress"]["status"] = f"Scanning {os.path.basename(path)}"

    # Run scan
    photos = scanner.scan_paths(folders, progress_callback=on_progress)
    
    # Run categorizer and face detection on new photos
    for photo in photos:
        # Detect faces if model available
        faces = face_engine.detect_faces(photo["path"])
        photo["faces"] = faces
        # Categorize
        photo["tags"] = categorizer.categorize_image(photo, faces=faces)
        cache.put(photo["path"], photo)

    cache.save()
    state["photos"] = photos

    # Calculate duplicate groups
    state["duplicate_groups"] = duplicate_engine.find_duplicates(photos)

    # Calculate similarity groups (balanced by default)
    state["similarity_groups"] = similarity_engine.find_similar_groups(photos, mode="balanced")

    # Cluster faces
    state["face_clusters"] = face_engine.cluster_faces()

    state["scan_progress"] = {"current": len(photos), "total": len(photos), "status": "completed"}
    return {
        "total_scanned": len(photos),
        "duplicate_groups": len(state["duplicate_groups"]),
        "similarity_groups": len(state["similarity_groups"]),
        "face_clusters": len(state["face_clusters"])
    }

@app.route('/api/scan/cancel', method='POST')
def cancel_scan():
    scanner.cancel()
    state["scan_progress"]["status"] = "cancelled"
    return {"status": "cancelled"}

# 3. Photos List & Filtering
@app.route('/api/photos', method='GET')
def get_photos():
    category = request.query.get('category')
    tag = request.query.get('tag')
    search = request.query.get('search', '').lower()

    filtered = state["photos"]
    if category and category != "All":
        filtered = [p for p in filtered if category in (p.get("tags") or [])]
    if search:
        filtered = [p for p in filtered if search in p.get("filename", "").lower()]

    return {"photos": filtered, "total": len(filtered)}

# 4. Duplicates API
@app.route('/api/duplicates', method='GET')
def get_duplicates():
    return {"groups": state["duplicate_groups"]}

# 5. Visual Similarity API
@app.route('/api/similarity', method='GET')
def get_similarity():
    mode = request.query.get('mode', 'balanced')
    if mode in ["strict", "balanced", "loose"]:
        state["similarity_groups"] = similarity_engine.find_similar_groups(state["photos"], mode=mode)
    return {"groups": state["similarity_groups"], "mode": mode}

# 6. Face Clusters API
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

# 7. Safe Cleanup & Recycle Bin API
@app.route('/api/cleanup/recycle', method='POST')
def recycle_files():
    data = request.json or {}
    file_paths = data.get("files", [])
    if not file_paths:
        response.status = 400
        return {"error": "No files selected."}

    result = organizer.safe_delete_files(file_paths)
    
    # Remove from state
    recycled_set = set(result.get("recycled_files", []))
    state["photos"] = [p for p in state["photos"] if p["path"] not in recycled_set]
    
    # Recalculate duplicates & similarity
    state["duplicate_groups"] = duplicate_engine.find_duplicates(state["photos"])
    state["similarity_groups"] = similarity_engine.find_similar_groups(state["photos"])

    return result

# 8. Organization Plan & Execution API
@app.route('/api/organize/plan', method='POST')
def plan_organization():
    data = request.json or {}
    target_root = data.get("target_root")
    group_by = data.get("group_by", "category")
    action = data.get("action", "copy")

    if not target_root:
        response.status = 400
        return {"error": "Target directory is required."}

    plan = organizer.generate_plan(
        photos=state["photos"],
        target_root=target_root,
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

# 9. AI Settings & Secure Key Storage API
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
    enabled = data.get("enabled", False)

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
    provider = data.get("provider")
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

# 10. Thumbnail & File Serving
@app.route('/thumbnail/<path:path>')
def serve_thumbnail(path):
    cache_dir = os.path.abspath(".photovault_cache/thumbnails")
    return static_file(path, root=cache_dir)

@app.route('/local-image/<path:path>')
def serve_local_image(path):
    # Drive letter handling for Windows (e.g. D:/photos)
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
    dist_dir = os.path.abspath("dist")
    if os.path.exists(os.path.join(dist_dir, path)):
        return static_file(path, root=dist_dir)
    # Fallback to src if dist not yet built
    src_dir = os.path.abspath("src")
    if os.path.exists(os.path.join(src_dir, path)):
        return static_file(path, root=src_dir)
    return static_file("index.html", root=src_dir)

def run_desktop_app():
    import webview
    import threading

    # Start bottle server in background daemon thread
    server_thread = threading.Thread(
        target=lambda: run(app, host="127.0.0.1", port=54321, quiet=True),
        daemon=True
    )
    server_thread.start()

    # Desktop API for native OS interactions (folder picker)
    class DesktopAPI:
        def select_folder(self):
            window = webview.windows[0]
            result = window.create_file_dialog(webview.FOLDER_DIALOG)
            if result and len(result) > 0:
                return result[0]
            return None

    api = DesktopAPI()
    window = webview.create_window(
        title="PhotoVault Local AI",
        url="http://127.0.0.1:54321",
        width=1280,
        height=820,
        min_size=(1024, 700),
        js_api=api
    )
    webview.start(debug=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PhotoVault Local AI")
    parser.add_argument("--desktop", action="store_true", help="Launch native desktop window")
    parser.add_argument("--port", type=int, default=54321, help="Server port (default: 54321)")
    args = parser.parse_args()

    if args.desktop:
        run_desktop_app()
    else:
        print(f"[PhotoVault] Starting local API server at http://127.0.0.1:{args.port}...")
        run(app, host="127.0.0.1", port=args.port, reloader=False)
