from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import base64
import os

class BaseVisionAdapter(ABC):
    """
    Abstract base class for all external AI vision adapters.
    Strictly disabled by default; requires explicit user enablement.
    """

    def __init__(
        self,
        name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        is_enabled: bool = False
    ):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.is_enabled = is_enabled

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Tests API authentication and reachability."""
        pass

    @abstractmethod
    def analyze_images(
        self,
        image_paths: List[str],
        prompt: str,
        send_thumbnails: bool = True
    ) -> Dict[str, Any]:
        """
        Sends user-approved images to external vision API.
        Must check is_enabled before executing.
        """
        pass

    def encode_image_base64(self, image_path: str, max_dim: int = 512) -> Optional[str]:
        """Encodes local image to base64 string with optional thumbnail downsampling."""
        if not os.path.exists(image_path):
            return None
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            print(f"[Adapter {self.name}] Error encoding image {image_path}: {e}")
            return None
