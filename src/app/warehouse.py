"""Databricks SQL warehouse access.

Two auth paths:
- Deployed app with user authorization: pass the per-request OBO token
  (``x-forwarded-access-token``) -> queries run as the signed-in user.
- Local dev / app service-principal fallback: no token -> ``Config()`` resolves
  credentials from the active profile / injected SP env vars.

The OBO token is used transiently to open one connection and is never stored,
logged, or returned.
"""
import os
import time
from typing import Any

from databricks import sql
from databricks.sdk.core import Config

from config import get_logger

logger = get_logger(__name__)
_cfg: Config | None = None

# Each query opens its own short-lived session; under a burst of requests
# (plan load + profile save + phase switches) the warehouse can transiently
# reject an OpenSession (RequestError) or hit a Delta MERGE conflict
# (concurrent write). These are safe to retry; deterministic errors are not.
_MAX_ATTEMPTS = 4
_RETRY_BASE_SLEEP = 0.6  # seconds, exponential backoff


def _is_transient(err: Exception) -> bool:
    if isinstance(err, sql.exc.RequestError):
        return True  # network / OpenSession hiccup
    if isinstance(err, sql.exc.ServerOperationError):
        return "concurrent" in str(err).lower()  # Delta MERGE conflict
    return False


def _config() -> Config:
    # Lazy so importing this module never triggers SDK/network init -> fast startup.
    global _cfg
    if _cfg is None:
        _cfg = Config()
    return _cfg


def _http_path() -> str:
    warehouse_id = os.environ["DATABRICKS_WAREHOUSE_ID"]
    return f"/sql/1.0/warehouses/{warehouse_id}"


def query(
    sql_text: str,
    params: dict | list | None = None,
    user_token: str | None = None,
) -> list[dict[str, Any]]:
    """Run a query and return rows as a list of dicts."""
    cfg = _config()
    kwargs: dict[str, Any] = {
        "server_hostname": cfg.host,
        "http_path": _http_path(),
    }
    if user_token:
        # Deployed app: on-behalf-of the signed-in user.
        kwargs["access_token"] = user_token
    else:
        # Local / SP fallback.
        kwargs["credentials_provider"] = lambda: cfg.authenticate

    logger.info("warehouse query start (obo=%s): %s", bool(user_token), sql_text[:120])
    started = time.monotonic()
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            with sql.connect(**kwargs) as conn, conn.cursor() as cur:
                cur.execute(sql_text, params)
                if cur.description is None:
                    logger.info("warehouse query ok: 0 rows in %d ms", int((time.monotonic() - started) * 1000))
                    return []
                cols = [c[0] for c in cur.description]
                rows = [dict(zip(cols, row)) for row in cur.fetchall()]
                logger.info("warehouse query ok: %d rows in %d ms", len(rows), int((time.monotonic() - started) * 1000))
                return rows
        except Exception as err:  # noqa: BLE001 - classify, then retry or re-raise
            if attempt < _MAX_ATTEMPTS and _is_transient(err):
                sleep_s = _RETRY_BASE_SLEEP * (2 ** (attempt - 1))
                logger.warning("warehouse query transient error (attempt %d/%d), retrying in %.1fs: %s",
                               attempt, _MAX_ATTEMPTS, sleep_s, str(err)[:160])
                time.sleep(sleep_s)
                continue
            raise
