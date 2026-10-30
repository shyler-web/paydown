# Free deployment (no domain, no VM)

**Stack (all free, no credit card):**

| Piece | Service | Free URL |
|---|---|---|
| Frontend (static) | Vercel Hobby | `https://<name>.vercel.app` |
| Backend (Docker) | Render free web service | `https://<name>.onrender.com` |
| Graph DB | FalkorDB Cloud **Free** tier | `host:port` (no TLS) |

You do **not** need to buy a domain or rent a VM. Vercel and Render provide free
subdomains with HTTPS.

> **Free-tier caveats**
> - **FalkorDB Cloud Free:** 100 MB RAM, **no TLS**, stops after **1 day idle**, is
>   **deleted after 7 days idle**. Use a small demo repo (e.g.
>   `volcano-monitoring-system`), and add the keep-alive cron in step 4.
> - **Render free:** 512 MB, sleeps after 15 min idle, ~1 min to wake.
> - **Vercel Hobby:** static only (perfect for the React build).

---

## 1. FalkorDB Cloud (free)

1. Sign up at <https://app.falkordb.cloud/signup> (no card).
2. Create a **Free** instance (AWS or GCP).
3. Copy the **host** and **port** (and username/password if shown).

Free tier has **no TLS**, which matches the backend's plain host/port config.

---

## 2. Backend on Render (free web service)

1. Push this repo to GitHub.
2. Render → **New → Web Service** → connect the repo.
3. Settings:
   - **Environment:** Docker
   - **Dockerfile path:** `backend/Dockerfile`
   - **Docker build context:** `.` (repo root)
   - **Plan:** Free
   - **Health check path:** `/` (do **not** use `/api/health`; that needs FalkorDB)
4. Environment variables:
   ```bash
   FALKORDB_HOST=<falkordb-host>
   FALKORDB_PORT=<falkordb-port>
   FALKORDB_USERNAME=            # only if the free instance shows one
   FALKORDB_PASSWORD=
   FALKORDB_SSL=false            # set true if the instance requires TLS
   FALKORDB_TIMEOUT=5            # fail fast instead of hanging
   # FALKORDB_URL=redis://user:pass@host:port   # alternative to host/port
   NEBIUS_API_KEY=<your key>
   NEBIUS_MODEL=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B
   AI_ENABLED=true
   DEMO_ACCESS_CODE=<a code for judges>
   DEMO_MAX_CALLS_PER_DAY=100
   CLARIFY_PUBLISH_ENABLED=false
   CORS_ORIGINS=https://<your-app>.vercel.app
   ```
5. Deploy. Note the URL: `https://<name>.onrender.com`.
6. Smoke test:
   ```bash
   curl https://<name>.onrender.com/api/llm/info
   ```

The backend Dockerfile honors Render's `$PORT`, so no port change is needed.

> **If `/api/health` hangs or returns 503:** the FalkorDB values are wrong or the
> instance needs TLS. Double-check host (no `redis://`, no `:port`) and port, then
> try `FALKORDB_SSL=true`. Health now times out after `FALKORDB_TIMEOUT` seconds
> (default 5) instead of hanging.

---

## 3. Frontend on Vercel (free)

1. Vercel → **New Project** → import the repo.
2. Framework preset: **Vite**. Build command `npm run build`, output `dist`.
3. Environment variable (Production + Preview):
   ```bash
   VITE_API_BASE=https://<name>.onrender.com
   ```
   Vite inlines this at **build time**, so set it **before** the first deploy and
   redeploy if it changes.
4. Deploy. Open `https://<your-app>.vercel.app`.

Because the frontend calls the Render URL, `CORS_ORIGINS` on Render must equal the
Vercel origin (step 2.4).

---

## 4. Keep FalkorDB alive (free GitHub Action)

FalkorDB's free instance stops after 1 day idle and is deleted after 7 days. Add
`.github/workflows/falkordb-keepalive.yml` (and set the repo secrets
`FALKORDB_HOST`, `FALKORDB_PORT`):

```yaml
name: falkordb-keepalive
on:
  schedule:
    - cron: "0 6 * * *"
  workflow_dispatch:
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install falkordb
      - run: |
          python - <<'PY'
          import os
          from falkordb import FalkorDB
          db = FalkorDB(host=os.environ["FALKORDB_HOST"], port=int(os.environ["FALKORDB_PORT"]))
          g = db.select_graph("graphhacks_health")
          print(g.query("RETURN 1").result_set)
          PY
        env:
          FALKORDB_HOST: ${{ secrets.FALKORDB_HOST }}
          FALKORDB_PORT: ${{ secrets.FALKORDB_PORT }}
```

---

## 5. Verify

```bash
curl https://<name>.onrender.com/api/llm/info
curl "https://<name>.onrender.com/api/clarify/analyze?repo=requests&limit=3"
```

Open the Vercel URL → paste `https://github.com/psf/requests` → **Load repo** → enter
the demo access code → Analyze / Memory work; Refactor Propose/Explain use Nebius.

---

## Security checklist

- [ ] `DEMO_ACCESS_CODE` set; give it to judges in Devpost testing notes.
- [ ] `DEMO_MAX_CALLS_PER_DAY` set; Nebius balance low.
- [ ] `CLARIFY_PUBLISH_ENABLED=false`; **no `GITHUB_TOKEN`** on Render.
- [ ] `CORS_ORIGINS` = the exact Vercel origin.
- [ ] `/api/health` is public (it only returns a node count) — fine.
- [ ] Rotate/revoke the Nebius key after judging.

---

## Instant alternative (not durable)

For a quick look right now, run the app locally and expose it with a free
Cloudflare quick tunnel:

```bash
docker compose up -d --build
cloudflared tunnel --url http://localhost:5173
# prints a public https://<random>.trycloudflare.com URL
```

This needs no domain and no VM, but the URL dies when you stop the tunnel — use it
for testing, not for judging.
