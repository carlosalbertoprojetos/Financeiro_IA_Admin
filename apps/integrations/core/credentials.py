import base64
import hashlib
import logging
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

logger = logging.getLogger(__name__)

SENSITIVE_CREDENTIAL_KEYS = ("api_key", "api_token")
ENCRYPTED_FLAG = "_encrypted"


def _fernet() -> Fernet:
    raw_key = getattr(settings, "INTEGRATION_CREDENTIALS_KEY", "") or ""
    if raw_key:
        return Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)

    derived = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    key = base64.urlsafe_b64encode(derived)
    logger.warning(
        "INTEGRATION_CREDENTIALS_KEY not set; deriving encryption key from SECRET_KEY"
    )
    return Fernet(key)


def encrypt_value(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Unable to decrypt stored credential") from exc


def encrypt_credentials(credentials: dict[str, Any]) -> dict[str, Any]:
    """Encrypt sensitive credential fields before persisting."""
    stored = dict(credentials)
    for key in SENSITIVE_CREDENTIAL_KEYS:
        value = stored.get(key)
        if value:
            stored[key] = encrypt_value(str(value))
    stored[ENCRYPTED_FLAG] = True
    return stored


def decrypt_credentials(credentials: dict[str, Any] | None) -> dict[str, Any]:
    """Decrypt sensitive credential fields when reading from storage."""
    if not credentials:
        return {}

    decrypted = dict(credentials)
    if not decrypted.get(ENCRYPTED_FLAG):
        return decrypted

    for key in SENSITIVE_CREDENTIAL_KEYS:
        value = decrypted.get(key)
        if value:
            decrypted[key] = decrypt_value(str(value))
    return decrypted
