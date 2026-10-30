"""FastAPI dependencies for the demo safety layer (see ``app.security``)."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException

from . import security


def demo_code(x_demo_code: str | None = Header(default=None)) -> str | None:
    """Read the optional ``X-Demo-Code`` header."""
    return x_demo_code


def require_demo_code(code: str | None = Depends(demo_code)) -> str | None:
    """Require the access code when ``DEMO_ACCESS_CODE`` is configured."""
    try:
        security.require_access(code)
    except security.SecurityError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.detail) from exc
    return code


def require_ai(code: str | None = Depends(demo_code)) -> str | None:
    """Require access + AI enabled + daily budget for an LLM call."""
    try:
        security.check_ai_allowed(code)
    except security.SecurityError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.detail) from exc
    return code
