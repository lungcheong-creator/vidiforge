"""Pytest configuration."""

import os
import sys

# Make the api/ directory importable
API_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if API_ROOT not in sys.path:
    sys.path.insert(0, API_ROOT)

# Force a dev token for tests
os.environ.setdefault("VIDIFORGE_API_TOKEN", "test-token-12345678")
os.environ.setdefault("VIDIFORGE_MASTER_KEY", "ZmRldi1rZXktbm90LWZvci1wcm9kdWN0aW9uLXVzZS0xMjM0NTY3OA==")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("VIDIFORGE_ENV", "development")