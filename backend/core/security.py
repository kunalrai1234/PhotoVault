import keyring
from typing import Optional, Dict

SERVICE_NAME = "PhotoVault_Local_AI"

class CredentialVault:
    """
    Secure OS Credential Vault integration (Windows Credential Manager).
    Stores API keys securely in the OS vault; never in plain text, files, or repositories.
    """

    @staticmethod
    def get_api_key(provider_name: str) -> Optional[str]:
        try:
            return keyring.get_password(SERVICE_NAME, provider_name)
        except Exception as e:
            print(f"[Security] Failed to retrieve key for {provider_name}: {e}")
            return None

    @staticmethod
    def set_api_key(provider_name: str, api_key: str) -> bool:
        try:
            keyring.set_password(SERVICE_NAME, provider_name, api_key)
            return True
        except Exception as e:
            print(f"[Security] Failed to store key for {provider_name}: {e}")
            return False

    @staticmethod
    def delete_api_key(provider_name: str) -> bool:
        try:
            keyring.delete_password(SERVICE_NAME, provider_name)
            return True
        except Exception as e:
            print(f"[Security] Failed to delete key for {provider_name}: {e}")
            return False

    @staticmethod
    def mask_key(key: Optional[str]) -> str:
        if not key or len(key) < 8:
            return "••••••••"
        return f"{key[:3]}••••••••{key[-4:]}"
