# Oracle Cloud Always Free VM (Docker + Caddy)

This is the **no-sleep, no-100 MB-cap** option: a real VM you control, free forever
within Oracle's Always Free limits. Use it when the free managed stack (Render +
FalkorDB Cloud free) is too small.

**Will it work?** Yes with the **Arm** shape (`VM.Standard.A1.Flex`, 2 OCPU / 12 GB).
The AMD micro (`VM.Standard.E2.1.Micro`, 1 GB) may run out of memory with FalkorDB.

**Time:** ~30–60 min if account verification is instant; signup review and Arm
capacity can add hours.

---

## 0. Prerequisites

- Oracle Cloud account (card + phone for identity verification; Always Free is not
  charged unless you upgrade).
- An SSH key pair.
- A free hostname (no domain purchase):
  - **sslip.io** — instant: `<public-ip-with-dashes>.sslip.io` (e.g.
    `140-238-10-5.sslip.io`).
  - or **DuckDNS** — `yourname.duckdns.org` (run the updater if the IP changes).

---

## 1. Create the VM

1. Oracle Console → **Compute → Instances → Create instance**.
2. **Image:** Ubuntu 22.04 or 24.04.
3. **Shape:** `VM.Standard.A1.Flex` → **2 OCPUs / 12 GB** (Always Free).
   - If Arm capacity is unavailable, retry another availability domain, or use
     `VM.Standard.E2.1.Micro` (1 GB — expect memory pressure).
4. **Networking:** create/select a VCN with a public subnet; assign a **public IPv4**.
5. **SSH keys:** upload your public key.
6. **Boot volume:** default (~50 GB) is fine.
7. Create, then copy the **public IP**.

> If the public IP can change after a stop/start, reserve one if Oracle offers it,
> or use DuckDNS and update the record.

---

## 2. Open ports 80 and 443 (both places!)

Oracle blocks traffic in **two** layers. Do both.

**A. VCN Security List**
VCN → Security Lists → default → **Add Ingress Rules**:
- `0.0.0.0/0`, TCP, destination port **80**
- `0.0.0.0/0`, TCP, destination port **443**
- (keep SSH 22 restricted to your IP)

**B. VM firewall (Ubuntu images ship with iptables rules)**

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

(If your image uses `ufw`: `sudo ufw allow 80,443/tcp`.)

---

## 3. Install Docker

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# log out/in (or `newgrp docker`) so docker works without sudo
docker --version
docker compose version
```

---

## 4. Deploy Paydown

```bash
git clone https://github.com/shyler-web/paydown.git
cd paydown

cat > .env <<'EOF'
NEBIUS_API_KEY=your_key
NEBIUS_MODEL=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B
TAVILY_API_KEY=your_key            # optional
DEMO_ACCESS_CODE=choose_a_code     # give this to judges
DEMO_MAX_CALLS_PER_DAY=100
DEMO_MAX_TOKENS_PER_CALL=2000
CLARIFY_PUBLISH_ENABLED=false
DOMAIN=140-238-10-5.sslip.io       # or yourname.duckdns.org
EOF

docker compose -f docker-compose.prod.yml up -d --build
```

What this does:

- FalkorDB and the backend publish **no host ports**.
- The frontend binds to `127.0.0.1:5173`.
- Caddy listens on **80/443**, gets a Let's Encrypt certificate for `DOMAIN`, and
  proxies to the frontend.

Watch the certificate:

```bash
docker compose -f docker-compose.prod.yml logs -f caddy
```

---

## 5. Verify

```bash
curl -I https://$DOMAIN
curl https://$DOMAIN/api/health
curl https://$DOMAIN/api/llm/info
```

Open the URL → paste `https://github.com/psf/requests` → **Load repo** → enter the
access code → Analyze / Memory / Refactor.

---

## 6. Keep it from being reclaimed

Oracle may reclaim an Always Free instance that stays below ~20% use for 7 days.
A small daily health check is enough for most accounts:

```bash
# add to crontab -e (daily)
0 6 * * * curl -fsS https://YOUR_DOMAIN/api/health >/dev/null
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Site unreachable | VCN ingress **and** iptables rules for 80/443 |
| Certificate not issued | DNS must point at the VM; port 80 open; check Caddy logs |
| `no space` / OOM builds | Use the Arm 12 GB shape; add swap if needed |
| `Out of host capacity` | Retry another AD/region, or use the AMD micro (1 GB) |
| Docker permission denied | `newgrp docker` or re-login after `usermod -aG docker` |
