"""Custom exception types used across services & controllers."""


class VidiForgeError(Exception):
    """Base exception."""


class ConfigError(VidiForgeError):
    """Configuration is missing or invalid (e.g., missing API key)."""


class ProviderError(VidiForgeError):
    """A third-party provider (LLM, TTS, etc.) returned an error."""


class TaskError(VidiForgeError):
    """Pipeline task failed at a specific stage."""


class SecurityError(VidiForgeError):
    """Token verification or decryption failed."""