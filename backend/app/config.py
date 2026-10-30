"""FalkorDB connection settings.

Secrets are never read here: only the non-secret host/port (and an optional
username/password if the environment provides one) are consumed via
``os.environ`` (AGENTS.md security rule). Never import or read ``.env``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6379
DEFAULT_TIMEOUT = 15.0


def _env_bool(name: str, default: bool = False) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class FalkorDBConfig:
    """Immutable connection settings resolved from the environment."""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    username: str | None = None
    password: str | None = None
    ssl: bool = False
    timeout: float = DEFAULT_TIMEOUT
    url: str | None = None

    @classmethod
    def from_env(cls) -> "FalkorDBConfig":
        host = os.environ.get("FALKORDB_HOST") or DEFAULT_HOST
        port_raw = os.environ.get("FALKORDB_PORT")
        try:
            port = int(port_raw) if port_raw else DEFAULT_PORT
        except ValueError:
            port = DEFAULT_PORT
        # Optional; absent for the local unauthenticated Docker instance.
        username = os.environ.get("FALKORDB_USERNAME") or None
        password = os.environ.get("FALKORDB_PASSWORD") or None
        # Managed instances may require TLS even on a free tier; default off.
        ssl = _env_bool("FALKORDB_SSL", False)
        # Fail fast instead of hanging a request when the DB is unreachable.
        try:
            timeout = float(os.environ.get("FALKORDB_TIMEOUT") or DEFAULT_TIMEOUT)
        except ValueError:
            timeout = DEFAULT_TIMEOUT
        if timeout <= 0:
            timeout = DEFAULT_TIMEOUT
        # Optional full connection string (redis://user:pass@host:port).
        url = (os.environ.get("FALKORDB_URL") or "").strip() or None
        return cls(
            host=host,
            port=port,
            username=username,
            password=password,
            ssl=ssl,
            timeout=timeout,
            url=url,
        )
