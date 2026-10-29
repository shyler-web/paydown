"""Bootstrap repo-scoped agent memory from *real* repository facts.

``repos.load_repo()`` calls :func:`bootstrap_repo_memory` after the code/company
graphs are built, so a freshly loaded repo gets its own tenant graph
(``tenant:repo-<slug>``) populated from real signals instead of the bundled demo
narrative. This is what makes the four-tier memory meaningful for an arbitrary
repo: the agent's memory is the audit trail of working on *that* code.

Tiers written (all idempotent — deterministic ids + ``MERGE``):

* **Episodic**  — load / ranking / playbook ``:Turn``s in a ``:Session``
* **Semantic**  — one ``:Entity``/``:Fact`` per worst file (A/B/E debt evidence)
* **Procedural** — the "safe one-file refactor" ``:Workflow``
* **Coordination** — analyzer → refactorer → validator → reviewer ``:Handoff``s
* **Projection** — one ``:ConceptNode`` per worst file for the cockpit

The A/B/E score is deterministic and tokenless (``cognitive_debt``); no LLM call
is made here. Safe to re-run (bootstrap is a refresh, not an append-spam).
"""

from __future__ import annotations

import time
from pathlib import Path

from . import db
from .cognitive_debt import FileRisk, rank_python_files
from .memory_service import MemoryService
from .models import (
    RecordHandoffInput,
    SaveWorkflowInput,
    StepInput,
    UpsertEntityInput,
    UpsertFactInput,
    WriteTurnInput,
)
from .observability import span

#: Cap the cockpit projection so a huge repo does not explode the graph.
MAX_CONCEPT_NODES = 40
#: Cap semantic facts to the worst files (the ones worth remembering).
MAX_FACTS = 10

#: Role agents for the refactor loop (generic — not the demo squad).
AGENTS: list[tuple[str, str, str, int]] = [
    ("agent:analyzer", "Analyzer", "Ranks Python files by comprehension risk", 3),
    ("agent:refactorer", "Refactorer", "Proposes a behaviour-preserving one-file refactor", 3),
    ("agent:validator", "Validator", "Runs frozen characterization tests in isolation", 4),
    ("agent:reviewer", "Reviewer", "Writes the intent note and reviewer question", 4),
]

_WORKFLOW_STEPS = [
    (1, "Freeze baseline + characterization tests on the original file", "Both phases pass on the original"),
    (2, "Propose one behaviour-preserving refactor via Nemotron (Nebius)", "Complete replacement source"),
    (3, "Run the frozen tests in an offline Docker sandbox", "All frozen tests pass"),
    (4, "Validate the score drop and reject complexity relocation", "Proposal accepted"),
    (5, "Write the intent note + reviewer question and prepare the PR", "PR_BODY.md ready"),
]


def repo_tenant(slug: str) -> str:
    """Tenant id for a repo's memory graph (``tenant:repo-<slug>``)."""
    return f"repo-{slug}"


def _domain_for(path: str) -> str:
    parts = Path(path).parts
    return parts[0] if len(parts) > 1 else "root"


def _required_level(score: float) -> int:
    """Minimum reader level needed to follow a file (higher debt → higher level)."""
    if score >= 70:
        return 5
    if score >= 55:
        return 4
    if score >= 40:
        return 3
    if score >= 25:
        return 2
    if score >= 10:
        return 1
    return 0


def _band(score: float) -> str:
    if score >= 70:
        return "Very hard to follow"
    if score >= 55:
        return "Hard to follow"
    if score >= 40:
        return "Moderately hard to follow"
    if score >= 25:
        return "Fairly clear"
    if score >= 10:
        return "Clear"
    return "Very clear"


def _register_tenant(tenant: str, name: str, slug: str) -> None:
    with db.named_graph(db.REGISTRY_GRAPH) as graph:
        graph.query(
            "MERGE (t:Tenant {key: $key}) SET t.name = $name, t.repo = $repo",
            params={"key": tenant, "name": name, "repo": slug},
        )


def _upsert_agents(tenant: str) -> None:
    with db.tenant_graph(tenant) as graph:
        for agent_id, name, role, level in AGENTS:
            graph.query(
                "MERGE (a:Agent {id: $id}) "
                "SET a.name = $name, a.role = $role, a.persona_level = $level",
                params={"id": agent_id, "name": name, "role": role, "level": level},
            )


def _upsert_concept_nodes(tenant: str, slug: str, files: list[FileRisk]) -> int:
    written = 0
    with db.tenant_graph(tenant) as graph:
        for idx, risk in enumerate(files[:MAX_CONCEPT_NODES]):
            a = risk.signals["A"].contribution
            b = risk.signals["B"].contribution
            e = risk.signals["E"].contribution
            graph.query(
                "MERGE (n:ConceptNode {id: $id}) "
                "SET n.domain = $domain, n.persona_level = $level, n.title = $title, "
                "n.summary = $summary, n.vibe_translation = $vibe, n.code_or_math = $code, "
                "n.status = $status, n.created_by_agent = $agent, n.repo = $repo, "
                "n.x = $x, n.y = $y",
                params={
                    "id": f"concept:{slug}:{risk.path}",
                    "domain": _domain_for(risk.path),
                    "level": _required_level(risk.score),
                    "title": risk.path,
                    "summary": (
                        f"{risk.path}: comprehension risk {risk.score:.1f}/100 — "
                        f"control flow {a:.1f}, size/branching {b:.1f}, missing docs {e:.1f}."
                    ),
                    "vibe": f"{_band(risk.score)} ({risk.score:.0f}/100 comprehension risk).",
                    "code": f"A={a:.1f} B={b:.1f} E={e:.1f} of 100 points",
                    "status": "ALERT" if risk.score >= 70 else "OK",
                    "agent": "AnalyzerAgent",
                    "repo": slug,
                    "x": 80 + (idx % 6) * 220,
                    "y": 80 + (idx // 6) * 120,
                },
            )
            written += 1
    return written


def _load_turn_text(display: str, slug: str, ranked: int, code_stats: dict[str, object] | None) -> str:
    parts = [f"Loaded repository {display} ({slug})."]
    if code_stats:
        for key in ("files", "symbols", "commits"):
            value = code_stats.get(key)
            if value is not None:
                parts.append(f"{value} {key}")
    parts.append(f"{ranked} Python files ranked by comprehension risk.")
    return " ".join(parts)


def bootstrap_repo_memory(
    slug: str,
    repo_path: str | Path,
    *,
    name: str | None = None,
    code_stats: dict[str, object] | None = None,
) -> dict[str, object]:
    """Create/refresh ``tenant:repo-<slug>`` from the repo's real signals."""
    repo = Path(repo_path).expanduser().resolve()
    if not repo.is_dir():
        raise ValueError(f"Repository directory does not exist: {repo}")

    with span("memory.bootstrap.rank"):
        ranking = rank_python_files(repo)
    files = ranking.files
    tenant = repo_tenant(slug)
    display = name or slug

    with span("memory.bootstrap.registry"):
        _register_tenant(tenant, display, slug)
        _upsert_agents(tenant)

    service = MemoryService()
    session_id = f"session:{slug}:load"

    service.write_turn(
        tenant,
        WriteTurnInput(
            id=f"turn:{slug}:load",
            role="agent",
            agent_id="agent:analyzer",
            session_id=session_id,
            topic="repo-load",
            text=_load_turn_text(display, slug, len(files), code_stats),
        ),
    )

    worst = files[0] if files else None
    service.write_turn(
        tenant,
        WriteTurnInput(
            id=f"turn:{slug}:debt",
            role="agent",
            agent_id="agent:analyzer",
            session_id=session_id,
            topic="cognitive-debt",
            text=(
                f"Ranked {len(files)} Python files by comprehension risk; "
                f"worst: {worst.path} at {worst.score:.1f}/100."
                if worst
                else "No rankable Python files found."
            ),
        ),
    )

    service.write_turn(
        tenant,
        WriteTurnInput(
            id=f"turn:{slug}:playbook",
            role="agent",
            agent_id="agent:refactorer",
            session_id=session_id,
            topic="safe-refactor",
            text=(
                "Safe one-file refactor playbook ready: freeze tests → propose → "
                "validate → prepare PR."
            ),
        ),
    )

    entity_ids: list[str] = []
    for risk in files[:MAX_FACTS]:
        entity_id = f"file:{slug}:{risk.path}"
        service.upsert_entity(
            tenant,
            UpsertEntityInput(id=entity_id, name=risk.path, type="File"),
        )
        service.upsert_fact(
            tenant,
            UpsertFactInput(
                id=f"debt:{slug}:{risk.path}",
                statement=(
                    f"{risk.path} has comprehension risk {risk.score:.1f}/100 "
                    f"(A={risk.signals['A'].contribution:.1f}, "
                    f"B={risk.signals['B'].contribution:.1f}, "
                    f"E={risk.signals['E'].contribution:.1f})."
                ),
                confidence=1.0,
                entity_id=entity_id,
                source_turn=f"turn:{slug}:debt",
            ),
        )
        entity_ids.append(entity_id)

    workflow_id = f"workflow:{slug}:safe-refactor"
    service.save_workflow(
        tenant,
        SaveWorkflowInput(
            id=workflow_id,
            name="Safe one-file refactor",
            trigger_domain="cognitive-debt",
            steps=[
                StepInput(order=order, action=action, expected_result=expected)
                for order, action, expected in _WORKFLOW_STEPS
            ],
            tool_ids=["tool:docker", "tool:nebius", "tool:git"],
        ),
    )

    now = int(time.time())
    target_entity = entity_ids[0] if entity_ids else None
    service.record_handoff(
        tenant,
        RecordHandoffInput(
            id=f"handoff:{slug}:bootstrap:analyze",
            created_at=now,
            reason="Ranked files; worst selected for refactor",
            status="COMPLETED",
            from_agent_id="agent:analyzer",
            to_agent_id="agent:refactorer",
            target_entity_id=target_entity,
        ),
    )
    service.record_handoff(
        tenant,
        RecordHandoffInput(
            id=f"handoff:{slug}:bootstrap:refactor",
            created_at=now,
            reason="A proposal must pass the frozen tests",
            status="PENDING",
            from_agent_id="agent:refactorer",
            to_agent_id="agent:validator",
            target_entity_id=target_entity,
        ),
    )
    service.record_handoff(
        tenant,
        RecordHandoffInput(
            id=f"handoff:{slug}:bootstrap:validate",
            created_at=now,
            reason="A validated proposal is ready for human review",
            status="PENDING",
            from_agent_id="agent:validator",
            to_agent_id="agent:reviewer",
            target_entity_id=target_entity,
        ),
    )

    concept_nodes = _upsert_concept_nodes(tenant, slug, files)

    return {
        "ok": True,
        "tenant": tenant,
        "repo": slug,
        "name": display,
        "files_ranked": len(files),
        "skipped": len(ranking.skipped),
        "worst": (
            {"path": worst.path, "score": round(worst.score, 2)} if worst else None
        ),
        "concept_nodes": concept_nodes,
        "facts": len(entity_ids),
        "workflow": workflow_id,
        "session": session_id,
    }
