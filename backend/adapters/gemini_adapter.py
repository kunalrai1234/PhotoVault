import requests
from typing import List, Dict, Any, Optional
from .base import BaseVisionAdapter

class GeminiAdapter(BaseVisionAdapter):
    """
    Google Gemini Vision Adapter.
    Uses active gemini-3.5-flash with automatic fallback.
    """

    SUPPORTED_MODELS = [
        "gemini-3.5-flash",
        "gemini-2.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-flash-latest"
    ]

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3.5-flash", is_enabled: bool = False):
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

        # Try active models
        models_to_try = [self.model_name] + [m for m in self.SUPPORTED_MODELS if m != self.model_name]
        for model in models_to_try:
            url = f"{self.base_url}/models/{model}?key={self.api_key}"
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    self.model_name = model
                    return {"success": True, "message": f"Successfully connected to Google Gemini ({model})!"}
            except Exception as e:
                print(f"[Gemini] Error connecting to {model}: {e}")

        return {"success": False, "message": "Failed to authenticate with Gemini API key."}

    def analyze_images(self, image_paths: List[str], prompt: str, send_thumbnails: bool = True) -> Dict[str, Any]:
        if not self.is_enabled:
            return {"success": False, "error": "Google Gemini adapter is disabled in Settings."}
        if not self.api_key:
            return {"success": False, "error": "No API key configured for Gemini."}

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
        models_to_try = [self.model_name] + [m for m in self.SUPPORTED_MODELS if m != self.model_name]

        last_err = "No response"
        for model in models_to_try:
            url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
            try:
                resp = requests.post(url, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    self.model_name = model
                    return {"success": True, "analysis": text, "model": model}
                elif resp.status_code in (404, 503):
                    last_err = f"HTTP {resp.status_code}: {resp.text[:150]}"
                    continue
                else:
                    return {"success": False, "error": f"API Error {resp.status_code}: {resp.text[:200]}"}
            except Exception as e:
                last_err = str(e)
                continue

        return {"success": False, "error": f"Gemini request failed: {last_err}"}
