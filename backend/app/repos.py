"""Any-repo loading (Option B) — paste a GitHub URL, then clone + graphify + load.

The "paste-a-link" seam for Track 01/03: ``POST /api/repos/load`` takes a
``https://github.com/<owner>/<repo>`` URL, shallow-clones it into a cache dir,
builds its AST graph with ``graphify update`` (no LLM), loads that graph into
FalkorDB ``code:<slug>`` (Track 01, via ``graph_sync.load_graph``) and ingests
commits/symbols/docs into ``company:brain`` (Track 03, via ``falkor_brain``),
then records a ``:Repo`` row in a registry graph so the frontend repo picker can
list what has been loaded.

Failure contract (matches ``app.main`` / ``app.routes_tracks``):

* **clone / graphify** failures are a 409 ``missing_artifact`` (the demo's
  prerequisite artifact could not be produced), never a 503.
* **FalkorDB** failures surface as 503 ``service_error`` (the rule-3 flip) so the
  cockpit shows its ErrorScreen and never silently falls back.

The ``main.py`` include of this router is wired by the integrator (W5); this
module only defines ``router`` and the importable ``load_repo`` function.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from redis.exceptions import ResponseError

from . import db
from .deps import require_demo_code
from .errors import missing_artifact, service_error
from .falkor_brain import FalkorBrain
from .graph_sync import load_graph
from .observability import span
from .repo_memory import bootstrap_repo_memory

router = APIRouter(prefix="/api/repos", tags=["repos"])

# Registry graph holding one ``:Repo`` row per loaded repository (the read-side
# mirror of D11's ``graphhacks_registry``; a separate graph so listing repos is
# a single bounded query and never reads every ``code:<slug>`` projection).
REPOS_GRAPH = "graphhacks_repos"

# Cache root for shallow clones. Overridable for containers/tests.
DEFAULT_CACHE_DIR = Path.home() / ".graphhacks-repos"

# A slug is the repo name lowercased with anything outside [a-z0-9_-] folded to
# ``-`` (never used in Cypher except as a *parameter* / ``code:<slug>`` key).
_SLUG_RE = re.compile(r"[^a-z0-9_-]+")
_SLUG_OK = re.compile(r"^[a-z0-9_-]{1,80}$")


class RepoLoadRequest(BaseModel):
    """Body of ``POST /api/repos/load``."""

    url: str = Field(..., min_length=1)


def _repo_name_and_slug(url: str) -> tuple[str, str]:
    """Extract the repo name and a ``[a-z0-9_-]`` slug from a GitHub URL.

    ``name`` is the human name (last path segment, ``.git`` stripped); ``slug``
    is the sanitised id used as the ``code:<slug>`` key and ``repo`` property.
    """
    parsed = urlparse(url)
    segments = [s for s in parsed.path.split("/") if s]
    name = segments[-1] if segments else "repo"
    if name.lower().endswith(".git"):
        name = name[:-4]
    slug = _SLUG_RE.sub("-", name.lower()).strip("-") or "repo"
    return name, slug


_ALLOWED_HOSTS = {"github.com", "www.github.com"}


def _validate_repo_url(url: str) -> None:
    """Only clone public GitHub HTTPS repos — never local paths or other hosts.

    Prevents SSRF / local-path clones on a public demo. ``git clone`` still runs
    as a subprocess, so the URL must be a plain repo URL with no credentials.
    """
    parsed = urlparse((url or "").strip())
    parts = [p for p in parsed.path.split("/") if p]
    if (
        parsed.scheme != "https"
        or parsed.netloc.lower() not in _ALLOWED_HOSTS
        or len(parts) != 2
        or "@" in parsed.netloc
    ):
        raise HTTPException(
            status_code=400,
            detail="only public https://github.com/<owner>/<repo> URLs are supported",
        )


def _cache_dir() -> Path:
    """Clone cache root; ``REPO_CACHE_DIR`` wins (containers/tests)."""
    return Path(os.environ.get("REPO_CACHE_DIR", str(DEFAULT_CACHE_DIR)))


def repo_cache_path(slug: str) -> Path:
    """Local clone path for a loaded repo (``<cache>/<slug>``)."""
    return _cache_dir() / slug


def _clone_repo(url: str, slug: str) -> Path:
    """Clone ``url`` (full history, so Track 03 ownership is real) into ``<cache>/<slug>``; 409 on failure."""
    target = _cache_dir() / slug
    try:
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        proc = subprocess.run(
            ["git", "clone", url, str(target)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:  # git binary missing / spawn failure
        raise missing_artifact(f"git clone failed for {url}: {exc}") from exc
    if proc.returncode != 0:
        raise missing_artifact(
            f"git clone failed for {url}: {proc.stderr.strip() or f'exit {proc.returncode}'}"
        )
    return target


def ensure_repo_clone(slug: str) -> Path:
    """Return the local clone, re-cloning from the registry if it vanished.

    Free hosts (Render) have no persistent disk: a restart drops
    ``<cache>/<slug>`` while the ``:Repo`` registry in FalkorDB survives. Re-clone
    on demand so Analyze/Refactor keep working without re-loading the URL.
    """
    path = repo_cache_path(slug)
    if path.is_dir():
        return path
    try:
        with span("repos.ensure_clone"):
            with db.named_graph(REPOS_GRAPH) as graph:
                result = graph.query(
                    "MATCH (r:Repo {id: $id}) RETURN r.url LIMIT 1",
                    params={"id": slug},
                )
                rows = result.result_set or []
    except Exception as exc:  # pragma: no cover - FalkorDB down
        raise service_error(exc) from exc
    url = str(rows[0][0]) if rows and rows[0] and rows[0][0] else ""
    if not url:
        raise missing_artifact(
            f"repo '{slug}' is not loaded; load its GitHub URL first"
        )
    _validate_repo_url(url)
    return _clone_repo(url, slug)


def delete_repo(slug: str) -> dict[str, object]:
    """Delete a repo: registry row, memory graph, code graph, and cached clone.

    ``company:brain`` rows are shared across repos and are left in place; they are
    no longer referenced by the repo picker once the ``:Repo`` row is gone.
    """
    if not _SLUG_OK.fullmatch(slug or ""):
        raise HTTPException(status_code=400, detail="invalid repo id")
    graphs = [db.repo_graph_key(slug), db.tenant_graph_key(f"repo-{slug}")]
    try:
        for key in graphs:
            with db.named_graph(key) as graph:
                try:
                    graph.delete()
                except ResponseError:
                    pass
        with db.named_graph(REPOS_GRAPH) as graph:
            graph.query(
                "MATCH (r:Repo {id: $id}) DELETE r",
                params={"id": slug},
            )
    except Exception as exc:  # pragma: no cover - exercised by stopping FalkorDB
        raise service_error(exc) from exc
    shutil.rmtree(repo_cache_path(slug), ignore_errors=True)
    return {"deleted": slug, "graphs": graphs}


def _graphify_repo(target: Path, slug: str) -> Path:
    """Build the AST graph via ``graphify update``; 409 on any failure."""
    try:
        proc = subprocess.run(
            ["graphify", "update", str(target)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:  # graphify binary missing
        raise missing_artifact(f"graphify unavailable: {exc}") from exc
    if proc.returncode != 0:
        raise missing_artifact(
            f"graphify failed for {slug}: {proc.stderr.strip() or f'exit {proc.returncode}'}"
        )
    graph_json = target / "graphify-out" / "graph.json"
    if not graph_json.is_file():
        raise missing_artifact(
            f"graphify produced no AST graph for {slug}: {graph_json}"
        )
    return graph_json


def _register_repo(slug: str, name: str, url: str) -> None:
    """MERGE the ``:Repo`` registry row (idempotent; ``loaded_at`` refreshed)."""
    at = int(time.time())
    with db.named_graph(REPOS_GRAPH) as graph:
        graph.query(
            "MERGE (r:Repo {id: $id}) "
            "SET r.name = $name, r.url = $url, r.loaded_at = $at",
            params={"id": slug, "name": name, "url": url, "at": at},
        )


def load_repo(url: str) -> dict[str, object]:
    """Clone + graphify + load one repo; the importable unit (no request object).

    Raises:
        HTTPException(409) — clone/graphify failed (missing artifact).
        HTTPException(503) — FalkorDB unavailable (rule-3 flip).
    """
    name, slug = _repo_name_and_slug(url)

    # Validate before any filesystem or subprocess work.
    _validate_repo_url(url)

    # Non-FalkorDB steps (clone / graphify). These raise 409 directly.
    target = _clone_repo(url, slug)
    graph_json = _graphify_repo(target, slug)

    # Every FalkorDB call is inside this block: a connection failure becomes 503.
    try:
        with span("repos.load"):
            stats = load_graph(graph_json, repo_id=slug, reset=True)

            brain = FalkorBrain()
            brain.ensure_schema()
            commits = brain.ingest_commits(slug, target)
            brain.ingest_symbols(slug, graph_json)
            brain.ingest_docs(slug, target)

            _register_repo(slug, name, url)

            # Repo-scoped agent memory (Phase 2): real Turns/Facts/Workflow/
            # Handoffs + ConceptNode projection in `tenant:repo-<slug>`. Best-effort
            # so a memory bug never fails the repo load; FalkorDB failures would
            # already have surfaced above.
            try:
                memory: dict[str, object] = bootstrap_repo_memory(
                    slug,
                    target,
                    name=name,
                    code_stats={
                        "files": stats.files,
                        "symbols": stats.symbols,
                        "commits": commits.commits,
                        "owners": commits.people,
                    },
                )
            except Exception as exc:  # pragma: no cover - defensive
                memory = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - exercised by stopping FalkorDB
        raise service_error(exc) from exc

    return {
        "repo_id": slug,
        "name": name,
        "url": url,
        "files": stats.files,
        "symbols": stats.symbols,
        "nodes_total": stats.nodes_total,
        "commits": commits.commits,
        "owners": commits.people,
        "memory": memory,
    }


@router.post("/load")
def api_load_repo(
    body: RepoLoadRequest, _code: str | None = Depends(require_demo_code)
) -> dict[str, object]:
    """Load an arbitrary GitHub repo into ``code:<slug>`` + ``company:brain``."""
    return load_repo(body.url)


@router.delete("/{slug}")
def api_delete_repo(
    slug: str, _code: str | None = Depends(require_demo_code)
) -> dict[str, object]:
    """Delete a repo's registry row, memory/code graphs, and cached clone."""
    return delete_repo(slug)


@router.get("")
def api_list_repos() -> dict[str, object]:
    """List every loaded repo, most recent first."""
    try:
        with span("repos.list"):
            with db.named_graph(REPOS_GRAPH) as graph:
                result = graph.query(
                    "MATCH (r:Repo) "
                    "RETURN r.id, r.name, r.url, r.loaded_at "
                    "ORDER BY r.loaded_at DESC"
                )
    except Exception as exc:  # pragma: no cover - exercised by stopping FalkorDB
        raise service_error(exc) from exc
    repos = [
        {"id": row[0], "name": row[1], "url": row[2], "loaded_at": row[3]}
        for row in (result.result_set or [])
    ]
    return {"repos": repos}
