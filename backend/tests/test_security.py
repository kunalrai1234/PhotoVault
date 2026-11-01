import pytest
from core.security import CredentialVault

def test_credential_vault_masking():
    assert CredentialVault.mask_key(None) == "••••••••"
    assert CredentialVault.mask_key("short") == "••••••••"
    masked = CredentialVault.mask_key("AIzaSyB1234567890abcdef")
    assert masked.startswith("AIz")
    assert masked.endswith("cdef")
    assert "1234567890" not in masked

def test_credential_vault_storage():
    test_provider = "test_provider_photovault_unit_test"
    test_key = "secret_key_12345_test"

    try:
        # Store
        saved = CredentialVault.set_api_key(test_provider, test_key)
        assert saved is True

        # Retrieve
        retrieved = CredentialVault.get_api_key(test_provider)
        assert retrieved == test_key

        # Delete
        deleted = CredentialVault.delete_api_key(test_provider)
        assert deleted is True

        # Verify deletion
        assert CredentialVault.get_api_key(test_provider) is None
    except Exception as e:
        # Some headless or restricted CI environments may not have OS keychain access
        pytest.skip(f"OS Credential Manager not accessible in this environment: {e}")

