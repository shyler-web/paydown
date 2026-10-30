# Submit Paydown — do these 5 things

Everything else is already built and pushed. Follow this in order. **≈45 minutes.**

---

## 1. Create the free graph DB (5 min)

<https://app.falkordb.cloud/signup> → **Free** instance (no card).
Copy the **host** and **port** (and username/password if shown).

---

## 2. Deploy the backend on Render (10 min)

Render → **New → Blueprint** → connect `shyler-web/paydown` → it reads `render.yaml`.
When prompted, paste:

| Variable | Value |
|---|---|
| `FALKORDB_HOST` | from step 1 |
| `FALKORDB_PORT` | from step 1 (`6379`) |
| `FALKORDB_USERNAME` / `PASSWORD` | from step 1 (blank if none) |
| `NEBIUS_API_KEY` | your key |
| `DEMO_ACCESS_CODE` | e.g. `judge2026` (tell judges this) |
| `CORS_ORIGINS` | leave blank for now; set after step 3 |

Deploy → copy the URL: `https://paydown-api.onrender.com`.

> If Blueprint isn't available: **New → Web Service** → Docker → Dockerfile
> `backend/Dockerfile`, context `.`, plan Free, health check `/`, same env vars.

---

## 3. Deploy the frontend on Vercel (10 min)

Vercel → **New Project** → import `shyler-web/paydown`.
- Framework: **Vite** · build `npm run build` · output `dist`
- Environment variable: `VITE_API_BASE=https://paydown-api.onrender.com`
- Deploy → copy `https://<your-app>.vercel.app`.

Now go back to Render → edit `CORS_ORIGINS` = `https://<your-app>.vercel.app` →
redeploy.

---

## 4. Test it (5 min)

Open the Vercel URL → paste a **small** repo (100 MB DB limit):

```
https://github.com/shyler-web/volcano-monitoring-system
```

- Enter the demo access code (top right).
- **Analyze** → debt, map, dependencies, owners.
- **Refactor** → pick a file → **Explain file** / **Propose refactor**.
- **Memory** → the repo's four tiers.

If `/api/health` is 503 → FalkorDB host/port is wrong.
If AI says “Nebius generation unavailable” → `NEBIUS_API_KEY` missing on Render.

---

## 5. Record the video (10 min) — under 3 minutes

| Time | Show |
|---|---|
| 0:00–0:15 | "Cognitive debt: code nobody can safely change." |
| 0:15–0:40 | Paste repo URL → Load → Analyze (debt index, worst files). |
| 0:40–1:20 | Refactor → Propose → validation checks + diff + intent note + **Nebius · model · ms** badge. |
| 1:20–1:50 | Explain file at **L0** then **L5** (same file, different reader). |
| 1:50–2:15 | Memory tab: episodes/facts/playbook/handoffs for this repo. |
| 2:15–2:40 | Say: runs on Nebius Token Factory with NVIDIA Nemotron; access code + budget guard. |
| 2:40–3:00 | Wrap: "Paydown — measure the debt, pay it down safely." |

Upload to **YouTube as Public**, copy the link.

---

## 6. Devpost (10 min)

- **Track:** Coding and Agentic Engineering
- **Demo URL:** your Vercel URL
- **Repo:** `https://github.com/shyler-web/paydown`
- **Video:** the public YouTube link
- **Testing instructions:** the URL + the `DEMO_ACCESS_CODE`.
- **Feedback:** per-key spend caps, usage/balance API + webhook alerts, per-key rate
  limits/scopes, publish account default RPM/TPM, document browser CORS.
- **What changed:** built on GraphHacks Nexus; added repo-scoped memory, Clarify
  analyze/propose/explain, 4-tab UI, Nebius proof, security guard.

---

## If something blocks you

| Blocker | Fast fallback |
|---|---|
| Render/FalkorDB signup issues | Oracle free VM (`docs/DEPLOY-ORACLE.md`) |
| FalkorDB 100 MB too small | use the small demo repo above |
| Free DB stops after 1 day idle | add the keep-alive workflow (`docs/DEPLOY-FREE.md`) |
| No time to host | record the video locally; submit the repo + video, and state the local run command |

**Do not add** `GITHUB_TOKEN`, mount a Docker socket, or enable publishing.
