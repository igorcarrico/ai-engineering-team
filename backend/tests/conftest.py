"""Test configuration.

Environment is set *before* application modules import so the cached settings
point at an isolated test database and run with zero mock latency.
"""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_aiteam.db")
os.environ.setdefault("MOCK_LATENCY_SECONDS", "0")
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("APP_ENV", "test")
