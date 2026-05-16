"""جلب الإعدادات من API لوحة التحكم مع cache."""
import os
import time
import httpx

API_BASE = os.getenv("API_BASE_URL", "").rstrip("/")
TOKEN = os.getenv("WORKER_TOKEN", "")

_cache = {"data": None, "ts": 0}
TTL = 30  # seconds


def get_config(force=False):
    now = time.time()
    if not force and _cache["data"] and now - _cache["ts"] < TTL:
        return _cache["data"]
    r = httpx.get(
        f"{API_BASE}/api/public/worker/config",
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=15,
    )
    r.raise_for_status()
    _cache["data"] = r.json()
    _cache["ts"] = now
    return _cache["data"]


def log_reply(payload):
    try:
        httpx.post(
            f"{API_BASE}/api/public/worker/log",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json=payload,
            timeout=10,
        )
    except Exception as e:
        print(f"[log] failed: {e}")


def heartbeat():
    try:
        httpx.post(
            f"{API_BASE}/api/public/worker/heartbeat",
            headers={"Authorization": f"Bearer {TOKEN}"},
            timeout=10,
        )
    except Exception as e:
        print(f"[hb] failed: {e}")
