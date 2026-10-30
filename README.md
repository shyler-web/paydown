# Paydown


## Live demo

- App: https://paydown-pearl.vercel.app
- Access code: `Nebiusjudge2026`
- Click **Demo repo**, wait for it to load, then use **Analyze / Refactor / Memory**.

**Pay down cognitive debt in any Python repo — analyze, refactor, and remember what the agents did.**

[![Nebius Token Factory](https://img.shields.io/badge/AI-Nebius%20Token%20Factory-22d3ee.svg)](https://tokenfactory.nebius.com/)
[![NVIDIA Nemotron](https://img.shields.io/badge/Model-NVIDIA%20Nemotron-76b900.svg)](https://www.nvidia.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite%20%2B%20TS-61DAFB.svg)](https://react.dev/)
[![FalkorDB](https://img.shields.io/badge/Memory-FalkorDB-red.svg)](https://www.falkordb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Paydown is an agentic developer cockpit for **cognitive debt**: the gap between what a
codebase is and what anyone understands it to be. Paste a public GitHub repo and
Paydown will:

1. **Score every Python file** with an explainable A/B/E comprehension-risk proxy.
2. **Show you where the pain is** — debt index, worst files, AST map, dependency
   hotspots, and ownership/docs context.
3. **Propose a safe refactor** of the worst file with **NVIDIA Nemotron** on
   **Nebius Token Factory**, then score-validate the change.
4. **Remember the work** in a per-repo, four-tier agent memory (episodic, semantic,
   procedural, coordination) stored in **FalkorDB**.

Built for the **Nebius × NVIDIA Global AI Hackathon** — **Coding & Agentic Engineering**
track.

---

## The problem

Agents and engineers can see one file at a time, but the expensive questions are about
relationships and history:

- Which file is nobody able to safely change?
- What breaks if this module changes?
- Who actually owns this code, and why does it exist?
- What did the agent try last time — and did it work?

Vector search cannot answer these. A graph can. Paydown makes comprehension debt
**measurable**, then pays it down **safely and explainably**, and keeps the agent's
work as durable memory.

---

## The app: four tabs

| Tab | What it does |
|---|---|
| **Analyze** | Repo debt index + worst files, AST repo map, dependency hotspots/blast radius (Track 01), ownership & docs (Track 03). Works **without an LLM key**. |
| **Refactor** | Rank files, **Propose refactor** (Nemotron), validation checks + diff + intent note + reviewer question, and **Explain file** at reader levels L0–L5. |
| **Memory** | The repo's four-tier agent memory: Episodic · Semantic · Procedural · Coordination. |
| **Status** | One-command setup, health checks, and what needs a key. |

### User journey

```
paste GitHub URL → Load repo
   → Analyze: debt index, worst files, repo map, dependencies, owners
   → Refactor: pick a file → Propose refactor → validation + diff + intent note
                → Explain file at L0…L5
   → Memory: see the run recorded as episodes, facts, a playbook, and handoffs
```

---

## Architecture

```
        Browser (React + Vite + TS)
                 │  /api
                 ▼
        FastAPI backend (Python 3.12, uv)
        ├── Clarify engine  → analyze / propose / explain
        ├── MemoryService   → episodic · semantic · procedural · coordination
        ├── ActionEngine    → dependency hotspots / blast radius
        ├── FalkorBrain     → ownership / docs / drift
        ├── LLM adapter     → Nebius Token Factory (NVIDIA Nemotron)
        └── Docker runner   → optional, offline, no secrets
                 │
                 ▼
        FalkorDB (memory + code graph + company brain)
```

**Named graphs (one FalkorDB instance):**

| Graph | Holds |
|---|---|
| `tenant:repo-<slug>` | The repo's four-tier agent memory + concept projection |
| `code:<slug>` | AST graph (files, symbols, CALLS/IMPORTS/CONTAINS/INHERITS) |
| `company:brain` | Git commits, authors, ownership, docs, drift |
| `graphhacks_registry` | Repo-scoped tenants (`:Tenant {key, name, repo}`) |
| `graphhacks_repos` | Loaded repos (`:Repo {id, name, url, loaded_at}`) |

---

## Nebius × NVIDIA — how the requirement is met

Every LLM feature is a **runtime call to Nebius Token Factory** with an **NVIDIA
Nemotron** open model, through a single adapter (`backend/app/llm.py`).

| Surface | Call site | What it does |
|---|---|---|
| Refactor proposal | `backend/app/clarify.py::propose_refactor` → `llm.generate_json` | Nemotron writes a behaviour-preserving replacement for one file |
| Reader-level explanation | `backend/app/clarify.py::explain_file` → `llm.chat_completion` | Explains the file at L0–L5 |
| Graph-grounded guidance | `backend/app/guidance.py` → `llm.chat_completion` | Explains the repo from real graph facts |
| Legacy proxy | `backend/app/main.py` `/api/llm/generate` (alias `/api/gemini/generate`) | Compatibility path |

Configuration:

```bash
NEBIUS_API_KEY=...     # server-side only; never shipped to the browser
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1   # default
NEBIUS_MODEL=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B       # default (NVIDIA)
```

Check your model id is available on your account:

```bash
cd backend
NEBIUS_API_KEY=... uv run python scripts/probe_nebius.py
```

`GET /api/llm/info` returns the provider, model, and configured flag (no secrets),
and the Refactor/Explain panels show a `Nebius Token Factory · <model> · <ms>` badge
on every live call.

---

## Quick start

### Prerequisites

- Docker + Docker Compose
- (Optional) a Nebius Token Factory API key for the AI features

### Run everything (one command)

```bash
docker compose up --build
```

Open **http://localhost:5173**, paste a public GitHub URL (for example
`https://github.com/psf/requests`), and press **Load repo**.

- **Works keyless:** Analyze + Memory (deterministic scoring + graph queries).
- **Needs `NEBIUS_API_KEY`:** Refactor → Propose / Explain, and graph-grounded guidance.
- FalkorDB Browser: **http://localhost:3000**.

### Enable the AI features

Create a root `.env` (never commit it):

```bash
NEBIUS_API_KEY=your_key
NEBIUS_MODEL=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B
TAVILY_API_KEY=your_key          # optional: research

# Optional demo safety (recommended for a public instance)
DEMO_ACCESS_CODE=judge           # judges type this in the UI code box
DEMO_MAX_CALLS_PER_DAY=100
DEMO_MAX_TOKENS_PER_CALL=2000
CLARIFY_PUBLISH_ENABLED=false
```

Then restart:

```bash
docker compose up -d --build
```

### Native development (optional)

```bash
# 1) FalkorDB
docker run -d --name falkordb -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest

# 2) Backend
cd backend
uv run uvicorn app.main:app --port 8000

# 3) Frontend (repo root)
npm install
npm run dev        # http://localhost:5173
```

---

## Deployment (public demo)

The local `docker-compose.yml` publishes FalkorDB on the host — fine for development,
not for the internet. For a public demo use the **production stack**, which exposes
only the TLS reverse proxy:

```bash
# on a small VM with a domain pointed at it
DOMAIN=paydown.example.com docker compose -f docker-compose.prod.yml up -d --build
```

- FalkorDB and the backend publish **no host ports** (internal network only).
- Caddy terminates HTTPS and renews certificates.
- `CLARIFY_PUBLISH_ENABLED=false`, no `GITHUB_TOKEN`, no Docker socket.
- Set `DEMO_ACCESS_CODE` and `DEMO_MAX_CALLS_PER_DAY` in `.env`; give the access code
  to judges.

Full runbook — **one VM + Caddy** or **Vercel + Render split** — with the security
checklist and smoke tests: **[`docs/DEPLOY.md`](./docs/DEPLOY.md)**.

**No domain or VM?** Use the free, no-card stack (Vercel + Render free + FalkorDB
Cloud free): **[`docs/DEPLOY-FREE.md`](./docs/DEPLOY-FREE.md)**.

**Prefer a real always-on VM (no sleep, no 100 MB cap)?** Oracle Cloud Always Free
(2 Arm OCPU / 12 GB) + a free sslip.io/DuckDNS hostname:
**[`docs/DEPLOY-ORACLE.md`](./docs/DEPLOY-ORACLE.md)**.

## The cognitive-debt score (A/B/E)

Each Python file gets a **0–100** risk score. It is deterministic and tokenless:

| Signal | Weight | What it measures |
|---|---|---|
| **A** control flow | 50% | Nesting depth, branches, loops, exceptions |
| **B** size & branching | 40% | File/function length and branch burden |
| **E** intent coverage | 10% | Missing module/function docstrings |

`debt_index` is the mean score across the repo's Python files (tests and generated
directories are excluded; files over 1 MB are skipped).

Example: `src/requests/models.py` = **A 40.9 + B 22.7 + E 3.2 = 66.8/100**.

---

## The refactor pipeline

1. **Analyze** — rank files worst-first (no LLM tokens).
2. **Propose** — Nemotron receives only the target file and its A/B/E breakdown and
   must return JSON with complete replacement source. It never returns shell commands.
3. **Validate** — the replacement must parse as Python, change the file, lower the
   overall score by ≥1 point, lower the structural A+B score by ≥1 point, and not
   simply move complexity into new helpers (anti-gaming).
4. **Human review** — Paydown returns the diff, a model-written intent note, one
   reviewer question, and the validation checks.

**Honest caveat (Option C):** the web path performs **score validation**, not
behaviour verification. The proposal is labelled **“Behavior not verified”**. The
strict path — frozen characterization tests run in an **offline Docker sandbox** —
exists in the engine and CLI (`backend/AGENT_WORKFLOW.md`) and is the next step for
the hosted flow. AI-generated code is **never executed on the host**.

---

## Agent memory: four tiers, per repo

When a repo is loaded, Paydown bootstraps `tenant:repo-<slug>` from **real** signals —
not a demo script:

| Tier | Contents |
|---|---|
| **Episodic** | `:Session` + `:Turn`s: repo loaded, files ranked, playbook ready, proposals |
| **Semantic** | `:Entity`/`:Fact` for the worst files with their A/B/E evidence |
| **Procedural** | A `:Workflow` “Safe one-file refactor” with ordered `:Step`s |
| **Coordination** | `:Handoff`s: analyzer → refactorer → validator → reviewer |

As you use the Refactor tab, new episodes, facts, and handoffs are appended. Loading
a different repo creates a separate memory graph, so memory never leaks across repos.

### Company brain

On load, the backend reads the cloned repo's **real** `git log`, docs, and symbols
into `company:brain` — who owns a file, why it exists (cited commits/docs), and what
drifted. This is real repository data, not hardcoded.

---

## API reference (selected)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | FalkorDB node count (`503` if down) |
| `GET` | `/api/tenants` | Repo-scoped memory tenants |
| `GET` | `/api/graph/nodes?tenant=` | Memory projection for a repo |
| `POST` | `/api/repos/load` | Clone + graphify + load a public GitHub repo |
| `POST` | `/api/memory/bootstrap?repo=` | Rebuild a repo's memory from its clone |
| `GET` | `/api/clarify/analyze?repo=` | A/B/E ranking |
| `POST` | `/api/clarify/refactor` | Propose + score-validate a refactor |
| `POST` | `/api/clarify/explain` | Explain a file at L0–L5 |
| `GET` | `/api/clarify/usage` | Today's AI calls/tokens vs limits |
| `GET` | `/api/llm/info` | Provider/model/configured (no secrets) |
| `POST` | `/api/llm/generate` | Provider proxy (alias `/api/gemini/generate`) |
| `GET` | `/api/track1/*` | Dependency hotspots/blast radius/graph |
| `GET` | `/api/track3/*` | Ownership, why-it-exists, drift |

---

## Security

| Layer | Implementation |
|---|---|
| Secrets | Read server-side only (`os.environ`); the browser never receives a key |
| Access code | `DEMO_ACCESS_CODE` → `X-Demo-Code` header (constant-time compare) |
| Budget guard | `AI_ENABLED` kill switch, `DEMO_MAX_CALLS_PER_DAY`, `DEMO_MAX_TOKENS_PER_CALL/DAY` |
| Repo loading | Only public `https://github.com/<owner>/<repo>` URLs (no local paths/SSRF) |
| AI code execution | Never on the host; Docker runs use `--network=none --read-only --cap-drop=ALL --user=65534 --no-new-privileges` |
| Publishing | `CLARIFY_PUBLISH_ENABLED=false` by default; no GitHub token in the demo |
| CORS | Off by default; opt-in via `CORS_ORIGINS` |
| Errors | Typed `400/403/409/422/429/503`; no secrets in messages |

---

## Verification

```bash
# Backend tests (43)
cd backend
uv run python -B -m unittest discover -s tests -q

# Frontend typecheck + production build
cd ..
npm run build

# Local smoke checks
curl http://localhost:5173/api/health
curl "http://localhost:5173/api/clarify/analyze?repo=requests&limit=5"
curl http://localhost:5173/api/llm/info
```

Expected: tests pass, build succeeds, Analyze/Memory work keyless, and AI endpoints
return `503` with a clear message when `NEBIUS_API_KEY` is absent.

---

## Limitations (honest)

- **Python-only** targets for scoring and refactoring.
- The web refactor path is **score-validated**, not behaviour-verified
  (“Behavior not verified” badge). The frozen-test/Docker path is CLI-only today.
- Docker validation needs an image that already contains the target repo's test
  dependencies (containers run offline).
- “Load any repo” needs the `graphify` CLI (installed in the backend image) and
  network access for `git clone`.
- No published per-key spend cap exists on Token Factory, so Paydown enforces its own
  budget guard.

---

## Track & submission

- **Event:** Nebius × NVIDIA Global AI Hackathon
- **Track:** Coding & Agentic Engineering
- **Repository:** public, MIT licensed
- **Demo video:** under 3 minutes, public on YouTube (shows a real proposal + the
  `Nebius Token Factory · <model> · <ms>` badge)
- **Feedback:** submitted on Devpost (per-key spend controls, usage alerts, model
  catalog clarity, CORS/key-safety documentation)

---

## AI assistant disclosure

AI coding assistants (Claude / Antigravity / Codex) were used under the author's
direct supervision. The author designed the architecture, the A/B/E scoring model,
the FalkorDB memory schema, and the validation rules; verified the Cypher and the
test suites; and is responsible for the correctness of the submitted code.

---

## Lineage

Paydown is the Nebius × NVIDIA submission and builds on the authors' earlier
**GraphHacks Nexus** (FalkorDB multi-agent memory cockpit) work. The graph engines,
memory service, and cockpit foundation were adapted into this product; the original
GraphHacks-only repository remains separate.

## License

[MIT](./LICENSE) © 2026 Kanhaiya
