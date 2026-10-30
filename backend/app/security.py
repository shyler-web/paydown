"""Demo safety controls: access code, AI budget, token cap, kill switch.

Token Factory enforces rate limits but has no documented **per-key spend cap**,
so the app enforces its own budget. Everything is env-driven and disabled by
default in a way that is safe for local dev:

* ``DEMO_ACCESS_CODE``            — when set, AI + repo-load calls require the
  ``X-Demo-Code`` header (judges get the code; the public cannot burn credits).
* ``AI_ENABLED``                  — ``false`` disables every LLM call (503).
* ``DEMO_MAX_CALLS_PER_DAY``      — hard cap on AI calls per UTC day (0 = off).
* ``DEMO_MAX_TOKENS_PER_CALL``    — per-request ``max_tokens`` sent to Nebius.
* ``DEMO_MAX_TOKENS_PER_DAY``     — hard cap on recorded tokens per UTC day (0 = off).
* ``CLARIFY_PUBLISH_ENABLED``     — must be ``true`` to ever open a PR (default off).

Counters are process-local (a single demo instance); a multi-worker deployment
would move them to FalkorDB. No secrets are logged.
"""

from __future__ import annotations

import hmac
import os
import threading
import time
from dataclasses import dataclass


class SecurityError(Exception):
    """A request failed a demo-safety check."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


def _env_bool(name: str, default: bool) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        return default


def access_code() -> str:
    return (os.environ.get("DEMO_ACCESS_CODE") or "").strip()


def ai_enabled() -> bool:
    return _env_bool("AI_ENABLED", True)


def max_calls_per_day() -> int:
    return _env_int("DEMO_MAX_CALLS_PER_DAY", 0)


def max_tokens_per_call(default: int = 2000) -> int:
    return _env_int("DEMO_MAX_TOKENS_PER_CALL", default)


def max_tokens_per_day() -> int:
    return _env_int("DEMO_MAX_TOKENS_PER_DAY", 0)


def publish_enabled() -> bool:
    """PR publishing is opt-in (never enabled on a public demo)."""
    return _env_bool("CLARIFY_PUBLISH_ENABLED", False)


@dataclass
class _Budget:
    day: str = ""
    calls: int = 0
    tokens: int = 0


_lock = threading.Lock()
_budget = _Budget()


def _today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _rollover_locked() -> None:
    today = _today()
    if _budget.day != today:
        _budget.day = today
        _budget.calls = 0
        _budget.tokens = 0


def require_access(code: str | None) -> None:
    """Reject the request when an access code is configured and does not match."""
    expected = access_code()
    if not expected:
        return
    provided = (code or "").strip()
    if not provided or not hmac.compare_digest(provided, expected):
        raise SecurityError(403, "invalid or missing demo access code (X-Demo-Code)")


def check_ai_allowed(code: str | None = None) -> None:
    """Enforce access code, kill switch, and the daily call/token budget."""
    require_access(code)
    if not ai_enabled():
        raise SecurityError(503, "AI features are disabled (AI_ENABLED=false)")
    limit_calls = max_calls_per_day()
    limit_tokens = max_tokens_per_day()
    with _lock:
        _rollover_locked()
        if limit_calls and _budget.calls >= limit_calls:
            raise SecurityError(429, "daily AI call budget reached; try again tomorrow")
        if limit_tokens and _budget.tokens >= limit_tokens:
            raise SecurityError(429, "daily AI token budget reached; try again tomorrow")


def record_ai_call(tokens: int = 0) -> None:
    """Count one successful AI call and its (estimated) tokens."""
    with _lock:
        _rollover_locked()
        _budget.calls += 1
        _budget.tokens += max(0, int(tokens))


def usage() -> dict[str, object]:
    """Current day's usage vs configured limits (safe to expose)."""
    with _lock:
        _rollover_locked()
        calls = _budget.calls
        tokens = _budget.tokens
    return {
        "day": _today(),
        "calls": calls,
        "tokens": tokens,
        "limits": {
            "max_calls_per_day": max_calls_per_day(),
            "max_tokens_per_call": max_tokens_per_call(),
            "max_tokens_per_day": max_tokens_per_day(),
            "ai_enabled": ai_enabled(),
            "access_code_required": bool(access_code()),
            "publish_enabled": publish_enabled(),
        },
    }


def reset_for_tests() -> None:
    """Clear the in-process budget (tests only)."""
    with _lock:
        _budget.day = _today()
        _budget.calls = 0
        _budget.tokens = 0
