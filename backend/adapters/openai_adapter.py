import requests
from typing import List, Dict, Any, Optional
from .base import BaseVisionAdapter

class OpenAIAdapter(BaseVisionAdapter):
    """
    OpenAI & OpenAI-compatible Vision Adapter (GPT-4o, OpenRouter, Local Ollama/vLLM).
    Disabled by default.
    """

    def __init__(
        self,
        name: str = "OpenAI",
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        model_name: str = "gpt-4o",
        is_enabled: bool = False
    ):
        super().__init__(
            name=name,
            api_key=api_key,
            base_url=base_url.rstrip("/"),
            model_name=model_name,
            is_enabled=is_enabled
        )

    def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "message": "API Key is missing."}

        url = f"{self.base_url}/models"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return {"success": True, "message": f"Successfully connected to {self.name}!"}
            return {"success": False, "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "message": f"Connection error: {e}"}

    def analyze_images(self, image_paths: List[str], prompt: str, send_thumbnails: bool = True) -> Dict[str, Any]:
        if not self.is_enabled:
            return {"success": False, "error": f"{self.name} adapter is disabled in Settings."}
        if not self.api_key:
            return {"success": False, "error": f"No API key configured for {self.name}."}

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        content_elements: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        for path in image_paths:
            b64 = self.encode_image_base64(path)
            if b64:
                content_elements.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": content_elements}],
            "max_tokens": 1000
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                msg = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"success": True, "analysis": msg}
            return {"success": False, "error": f"API Error {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": f"Request failed: {e}"}
