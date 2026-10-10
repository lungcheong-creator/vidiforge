"""Server-side encryption utilities using Fernet (AES-128-CBC + HMAC)."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config.config import settings
from app.models.exception import SecurityError

_FERNET: Fernet | None = None


def _get_fernet() -> Fernet:
    """Lazily instantiate a Fernet instance."""
    global _FERNET
    if _FERNET is not None:
        return _FERNET

    master = settings.vidiforge_master_key
    if not master:
        # Derive a stable but insecure key from the API token (dev fallback only).
        # In production, VIDIFORGE_MASTER_KEY MUST be set.
        if settings.vidiforge_env == "production":
            raise SecurityError(
                "VIDIFORGE_MASTER_KEY must be set in production for at-rest encryption."
            )
        digest = hashlib.sha256(settings.vidiforge_api_token.encode()).digest()
        master = base64.urlsafe_b64encode(digest).decode()

    try:
        _FERNET = Fernet(master.encode() if isinstance(master, str) else master)
    except (ValueError, TypeError) as e:
        raise SecurityError(f"Invalid VIDIFORGE_MASTER_KEY: {e}") from e

    return _FERNET


def encrypt(plaintext: str) -> bytes:
    """Encrypt a UTF-8 string. Returns base64-urlsafe-encoded ciphertext bytes."""
    if not plaintext:
        return b""
    return _get_fernet().encrypt(plaintext.encode("utf-8"))


def decrypt(ciphertext: bytes) -> str:
    """Decrypt ciphertext bytes back to a UTF-8 string."""
    if not ciphertext:
        return ""
    try:
        return _get_fernet().decrypt(ciphertext).decode("utf-8")
    except InvalidToken as e:
        raise SecurityError("Failed to decrypt value — invalid key or corrupted data.") from e


def mask(value: str) -> str:
    """Return a masked representation: first 4 + ellipsis + last 4."""
    if not value:
        return ""
    if len(value) <= 12:
        return "*" * len(value)
    return f"{value[:4]}…{value[-4:]}"