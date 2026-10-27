import requests
from typing import List, Dict, Any, Optional
from .base import BaseVisionAdapter

class GeminiAdapter(BaseVisionAdapter):
    """
    Google Gemini Vision Adapter (e.g. gemini-1.5-flash, gemini-2.5-flash).
    Disabled by default.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash", is_enabled: bool = False):
        super().__init__(
            name="Google Gemini",
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta",
            model_name=model_name,
            is_enabled=is_enabled
        )

    def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "message": "API Key is missing."}

        url = f"{self.base_url}/models/{self.model_name}?key={self.api_key}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return {"success": True, "message": f"Successfully connected to {self.model_name}!"}
            return {"success": False, "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "message": f"Connection error: {e}"}

    def analyze_images(self, image_paths: List[str], prompt: str, send_thumbnails: bool = True) -> Dict[str, Any]:
        if not self.is_enabled:
            return {"success": False, "error": "Google Gemini adapter is disabled in Settings."}
        if not self.api_key:
            return {"success": False, "error": "No API key configured for Gemini."}

        url = f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}"
        
        parts: List[Dict[str, Any]] = [{"text": prompt}]
        for path in image_paths:
            b64 = self.encode_image_base64(path)
            if b64:
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": b64
                    }
                })

        payload = {"contents": [{"parts": parts}]}
        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return {"success": True, "analysis": text}
            return {"success": False, "error": f"API Error {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": f"Request failed: {e}"}
