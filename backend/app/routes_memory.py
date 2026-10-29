"""Repo → agent-memory routes.

``POST /api/memory/bootstrap?repo=<slug>`` (re)builds the repo-scoped tenant
graph (``tenant:repo-<slug>``) from the repo's on-disk clone. It is normally
called automatically by ``POST /api/repos/load``; this endpoint lets the cockpit
refresh memory after a scan without re-cloning.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from .errors import missing_artifact, service_error
from .observability import span
from .repo_memory import bootstrap_repo_memory
from .repos import repo_cache_path

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.post("/bootstrap")
def api_memory_bootstrap(repo: str = Query(..., min_length=1)) -> dict[str, object]:
    """Bootstrap ``tenant:repo-<repo>`` from the repo's cloned files."""
    path = repo_cache_path(repo)
    if not path.is_dir():
        raise missing_artifact(
            f"repo '{repo}' is not loaded (no clone at {path}); POST /api/repos/load first"
        )
    try:
        with span("api.memory.bootstrap"):
            return bootstrap_repo_memory(repo, path, name=repo)
    except Exception as exc:  # pragma: no cover - exercised by stopping FalkorDB
        raise service_error(exc) from exc
