# Deploying Paydown safely

Two supported shapes. Pick **Option A** for the simplest single-URL demo, or
**Option B** if you prefer managed services.

## What is public vs private

```
Internet ──443──▶ Caddy (TLS) ──▶ frontend (nginx) ──/api──▶ backend ──▶ FalkorDB
                                   public                 private     private
```

- **Public:** only `80/443` (Caddy) — or the frontend origin in split hosting.
- **Never public:** FalkorDB (`6379`/`3000`), the FastAPI backend (`8000`), and the
  Docker socket (never mounted).
- **Secrets:** only in the backend environment. The browser never receives a key.

---

## Option A — One VM + Caddy (recommended)

**Needs:** a small Linux VM (1–2 vCPU, 2 GB RAM) with Docker, and a domain.

### 1. DNS
Point an `A` record for your hostname (e.g. `paydown.example.com`) at the VM IP.

### 2. Create `.env` on the VM (never commit it)

```bash
NEBIUS_API_KEY=your_key
NEBIUS_MODEL=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B
TAVILY_API_KEY=your_key            # optional

# Demo safety
DEMO_ACCESS_CODE=choose_a_code     # give this to judges
DEMO_MAX_CALLS_PER_DAY=100
DEMO_MAX_TOKENS_PER_CALL=2000
DEMO_MAX_TOKENS_PER_DAY=0          # 0 = no daily token cap
CLARIFY_PUBLISH_ENABLED=false

# TLS hostname
DOMAIN=paydown.example.com
```

### 3. Start the production stack

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Caddy obtains and renews a Let's Encrypt certificate automatically. FalkorDB and
the backend publish **no host ports**.

### 4. Firewall

Allow only `22` (optional, for SSH), `80`, and `443`. Do **not** open `6379`,
`3000`, or `8000`.

### 5. Verify

```bash
curl -I https://$DOMAIN
curl https://$DOMAIN/api/health          # {"status":"ok", ...}
curl https://$DOMAIN/api/llm/info        # provider/model/configured
```

Open the site, paste a repo URL, press **Load repo**, and enter the demo access
code in the top-right box.

> **TLS note:** Caddy needs `80/443` reachable and a correct DNS record before it
> can issue a certificate. Check logs with
> `docker compose -f docker-compose.prod.yml logs -f caddy`.

---

## Option B — Managed split (Vercel + Render)

Use this if you prefer managed hosting. **Vercel cannot host the Python backend.**

### FalkorDB (Render private service)
- New **Private Service** → Docker image `falkordb/falkordb:latest`.
- Keep it private (no public URL). Note its internal hostname.

### Backend (Render web service)
- New **Web Service** → this repo → **Docker** → `backend/Dockerfile`, root context.
- Environment:
  ```bash
  FALKORDB_HOST=<falkordb-private-hostname>
  FALKORDB_PORT=6379
  NEBIUS_API_KEY=...
  NEBIUS_MODEL=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B
  DEMO_ACCESS_CODE=choose_a_code
  DEMO_MAX_CALLS_PER_DAY=100
  CLARIFY_PUBLISH_ENABLED=false
  CORS_ORIGINS=https://<your-frontend>
  ```
- Do **not** set `GITHUB_TOKEN`. Do **not** mount a Docker socket.

### Frontend (Vercel static)
- Import the repo; build `npm run build`; output `dist`.
- Set `VITE_API_BASE=https://<backend-host>` at build time (the frontend calls that
  absolute URL; CORS is enabled by `CORS_ORIGINS`).
- Redeploy after setting the env var (Vite inlines it at build time).

---

## Security checklist (before sharing the link)

- [ ] `DEMO_ACCESS_CODE` is set; provide it to judges in the Devpost testing notes.
- [ ] `DEMO_MAX_CALLS_PER_DAY` is set (e.g. 100) and the Nebius balance is low.
- [ ] `CLARIFY_PUBLISH_ENABLED=false` and **no `GITHUB_TOKEN`** on the host.
- [ ] FalkorDB and the backend are **not** publicly reachable.
- [ ] HTTPS only; CORS limited to the frontend origin (split hosting).
- [ ] `.env` is not committed; the repo is public and MIT licensed.
- [ ] Rotate/revoke the Nebius key after judging.

---

## Post-deploy smoke test

```bash
curl -s https://$DOMAIN/api/health
curl -s https://$DOMAIN/api/llm/info
curl -s "https://$DOMAIN/api/clarify/analyze?repo=requests&limit=3"
# AI path (needs the access code if DEMO_ACCESS_CODE is set):
curl -s -H "X-Demo-Code: choose_a_code" -H 'Content-Type: application/json' \
  -d '{"repo":"requests","target":"src/requests/models.py"}' \
  https://$DOMAIN/api/clarify/refactor
```

Expected: `health` 200; `llm/info` shows `configured: true`; `analyze` returns a
ranking; `refactor` returns a proposal with a `Nebius Token Factory · <model> · <ms>`
provider block.

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| `502` | backend not running (`docker compose ... logs backend`) |
| `503 FalkorDB unavailable` | FalkorDB service down / wrong `FALKORDB_HOST` |
| `503 Nebius generation unavailable` | `NEBIUS_API_KEY` missing or invalid |
| `403 invalid or missing demo access code` | enter the code in the UI (top right) |
| browser CORS error (split hosting) | `CORS_ORIGINS` must equal the frontend origin |
| certificate not issued | DNS not pointing at the VM, or `80/443` closed |
