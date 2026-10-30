"""Clarify HTTP routes — analyze, propose, explain (Nebius + score validation)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from . import clarify, llm, security
from .deps import require_ai
from .errors import service_error
from .refactor_agent import AgentError

router = APIRouter(prefix="/api/clarify", tags=["clarify"])


class RefactorRequest(BaseModel):
    repo: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)


class ExplainRequest(RefactorRequest):
    level: int = Field(3, ge=0, le=5)


def _translate(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, llm.LLMUnavailable):
        return HTTPException(status_code=503, detail=f"LLM unavailable: {exc}")
    if isinstance(exc, AgentError):
        text = str(exc)
        if "unavailable" in text.lower():
            return HTTPException(status_code=503, detail=text)
        return HTTPException(status_code=422, detail=text)
    return service_error(exc)


@router.get("/usage")
def api_clarify_usage() -> dict[str, object]:
    """Today's AI usage vs limits (safe, no secrets)."""
    return security.usage()


@router.get("/analyze")
def api_clarify_analyze(
    repo: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=500),
) -> dict[str, object]:
    """Rank a loaded repo's Python files by the A/B/E comprehension-risk proxy."""
    try:
        return clarify.analyze_repo(repo, limit=limit)
    except Exception as exc:
        raise _translate(exc) from exc


@router.post("/refactor")
def api_clarify_refactor(
    body: RefactorRequest, _code: str | None = Depends(require_ai)
) -> dict[str, object]:
    """Propose a refactor and score-validate it (behavior verified only with Docker)."""
    try:
        result = clarify.propose_refactor(
            body.repo,
            body.target,
            max_tokens=security.max_tokens_per_call(),
        )
    except Exception as exc:
        raise _translate(exc) from exc
    security.record_ai_call(len(str(result.get("proposed_source", ""))) // 4)
    return result


@router.post("/explain")
def api_clarify_explain(
    body: ExplainRequest, _code: str | None = Depends(require_ai)
) -> dict[str, object]:
    """Explain one file at a reader level (L0..L5) via Nebius Nemotron."""
    try:
        result = clarify.explain_file(
            body.repo,
            body.target,
            level=body.level,
            max_tokens=security.max_tokens_per_call(),
        )
    except Exception as exc:
        raise _translate(exc) from exc
    security.record_ai_call(len(str(result.get("answer", ""))) // 4)
    return result
