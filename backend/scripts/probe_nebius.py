"""Probe Nebius Token Factory: list models and check the configured model id.

Reads ``NEBIUS_API_KEY`` from the environment and never prints it. Run from
``backend/``:

    uv run python scripts/probe_nebius.py

Exit codes: 0 = target model found, 1 = target model missing, 2 = probe failed.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = (
    os.environ.get("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1")
).rstrip("/")
KEY = (os.environ.get("NEBIUS_API_KEY") or "").strip()
TARGET = (
    os.environ.get("NEBIUS_MODEL") or "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"
).strip()


def main() -> int:
    if not KEY:
        print("NEBIUS_API_KEY is not set in the environment", file=sys.stderr)
        return 2
    req = urllib.request.Request(
        BASE + "/models", headers={"Authorization": f"Bearer {KEY}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        print(f"models endpoint error {exc.code}: {detail}", file=sys.stderr)
        return 2
    except Exception as exc:  # network / parse
        print(f"probe failed ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 2

    items = payload.get("data") or payload.get("models") or []
    ids = sorted(
        str(item.get("id") or item.get("name") or "")
        for item in items
        if isinstance(item, dict)
    )
    ids = [i for i in ids if i]
    print(f"base_url: {BASE}")
    print(f"models: {len(ids)}")
    for model_id in ids:
        mark = "  <-- target" if model_id == TARGET else ""
        print(f"  - {model_id}{mark}")
    found = TARGET in ids
    print(f"target: {TARGET} -> {'FOUND' if found else 'NOT FOUND'}")
    if not found:
        print(
            "Set NEBIUS_MODEL to one of the ids above (an NVIDIA model for the "
            "hackathon requirement).",
            file=sys.stderr,
        )
    return 0 if found else 1


if __name__ == "__main__":
    raise SystemExit(main())
