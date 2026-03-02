"""File-based snapshot cache — persists across container restarts.

Since ./backend is bind-mounted to /app in the container, any file written
under /app/snapshot_store/ lives in the workspace and survives docker restart,
docker-compose down/up, and deployments (as long as the volume/bind persists).

This is Tier 2 of the caching stack (between in-memory and Supabase):
  Tier 1 — in-memory  (snapshot_memory_cache.py)  sub-ms, process-scoped
  Tier 2 — file       (THIS MODULE)                ~1ms, survives restarts
  Tier 3 — Supabase   (snapshot_cache.py)          cross-process, DB-backed

File layout:
  /app/snapshot_store/
      <sha256-hash>.json    — one file per (farm_id, params, date) combination
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Default store dir — inside the bind-mounted /app directory so files persist
_DEFAULT_STORE_DIR = Path(
    os.getenv("SNAPSHOT_STORE_DIR", "/app/snapshot_store")
)

_DEFAULT_TTL_SECONDS = 4 * 60 * 60  # 4 hours


def _store_dir() -> Path:
    d = _DEFAULT_STORE_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def _file_path(params_hash: str) -> Path:
    return _store_dir() / f"{params_hash}.json"


def get(params_hash: str) -> Optional[Dict[str, Any]]:
    """Return the stored snapshot payload for *params_hash*, or None."""
    path = _file_path(params_hash)
    if not path.exists():
        logger.debug("File cache MISS %s", params_hash[:12])
        return None

    try:
        with path.open() as f:
            record = json.load(f)

        expires_at = record.get("expires_at", 0)
        if time.time() > expires_at:
            logger.info("File cache EXPIRED  %s…", params_hash[:12])
            path.unlink(missing_ok=True)
            return None

        logger.info("File cache HIT  %s…", params_hash[:12])
        return record["payload"]

    except Exception as e:
        logger.warning("File cache read error (%s): %s", params_hash[:12], e)
        return None


def put(
    params_hash: str,
    payload: Dict[str, Any],
    ttl_seconds: int = _DEFAULT_TTL_SECONDS,
) -> None:
    """Store *payload* keyed by *params_hash* with TTL."""
    path = _file_path(params_hash)
    try:
        record = {
            "params_hash": params_hash,
            "payload": payload,
            "stored_at": time.time(),
            "expires_at": time.time() + ttl_seconds,
        }
        tmp = path.with_suffix(".tmp")
        with tmp.open("w") as f:
            json.dump(record, f, default=str)
        tmp.rename(path)  # atomic write
        logger.info(
            "File cache SET  %s… (TTL %ds → %s)",
            params_hash[:12],
            ttl_seconds,
            path,
        )
    except Exception as e:
        logger.warning("File cache write error (%s): %s", params_hash[:12], e)


def invalidate(params_hash: str) -> None:
    """Delete the cached file for *params_hash*."""
    _file_path(params_hash).unlink(missing_ok=True)
    logger.info("File cache INVALIDATED  %s…", params_hash[:12])


def list_all() -> list[Dict[str, Any]]:
    """Return summary of all stored (non-expired) snapshot files (for debug)."""
    results = []
    try:
        now = time.time()
        for path in _store_dir().glob("*.json"):
            try:
                with path.open() as f:
                    rec = json.load(f)
                if rec.get("expires_at", 0) > now:
                    results.append(
                        {
                            "hash": path.stem[:12],
                            "stored_at": rec.get("stored_at"),
                            "expires_at": rec.get("expires_at"),
                            "size_bytes": path.stat().st_size,
                        }
                    )
            except Exception:
                pass
    except Exception as e:
        logger.warning("File cache list error: %s", e)
    return results
