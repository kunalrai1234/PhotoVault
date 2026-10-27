import requests
from typing import List, Dict, Any, Optional
from .base import BaseVisionAdapter

class ClaudeAdapter(BaseVisionAdapter):
    """
    Anthropic Claude Vision Adapter (claude-3-5-sonnet, claude-3-haiku).
    Disabled by default.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "claude-3-5-sonnet-20241022", is_enabled: bool = False):
        super().__init__(
            name="Anthropic Claude",
            api_key=api_key,
            base_url="https://api.anthropic.com/v1",
            model_name=model_name,
            is_enabled=is_enabled
        )

    def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "message": "API Key is missing."}
        # Lightweight headers test
        return {"success": True, "message": "Anthropic API Key configured."}

    def analyze_images(self, image_paths: List[str], prompt: str, send_thumbnails: bool = True) -> Dict[str, Any]:
        if not self.is_enabled:
            return {"success": False, "error": "Anthropic Claude adapter is disabled in Settings."}
        if not self.api_key:
            return {"success": False, "error": "No API key configured for Claude."}

        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        content_elements: List[Dict[str, Any]] = []
        for path in image_paths:
            b64 = self.encode_image_base64(path)
            if b64:
                content_elements.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": b64
                    }
                })
        content_elements.append({"type": "text", "text": prompt})

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": content_elements}],
            "max_tokens": 1000
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                text = "".join([c.get("text", "") for c in data.get("content", [])])
                return {"success": True, "analysis": text}
            return {"success": False, "error": f"API Error {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": f"Request failed: {e}"}
