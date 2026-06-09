"""Profile persistence — a Delta table in our writable UC schema (``team7``),
read/written through the SQL warehouse, with an in-memory fallback.

When a real warehouse is configured (``DATABRICKS_WAREHOUSE_ID``), profiles live in
``<catalog>.<team_schema>.user_profiles``. Reads/writes run **on-behalf-of the signed-in
user** (their forwarded ``sql`` token) — every real user is in ``account users``, which
holds USE SCHEMA / CREATE TABLE / SELECT / MODIFY on ``team7``, so no service-principal
grant is needed. Without a user token (local dev) the warehouse layer falls back to the
profile/SP credentials. When no real warehouse exists (tests, warehouse-less runs) a
process-local dict stands in so the API works end-to-end.

Arrays (diets/allergies) are stored as JSON strings to avoid SQL array-parameter
quirks. No credentials are handled here; auth is delegated to ``warehouse.query``.
"""
import copy
import json
import threading

import warehouse
from config import get_logger, settings

logger = get_logger(__name__)

_DEFAULT_ENERGY_TARGET = 2000
_CAL_MIN, _CAL_MAX = 1400, 3200


# --- backend selection -------------------------------------------------------
def _use_warehouse() -> bool:
    return settings.profile_persistence


# --- schema (created once, lazily) -------------------------------------------
_schema_lock = threading.Lock()
_schema_ready = False


def _ensure_schema(user_token: str | None) -> None:
    global _schema_ready
    if _schema_ready:
        return
    with _schema_lock:
        if _schema_ready:
            return
        warehouse.query(
            f"""
            CREATE TABLE IF NOT EXISTS {settings.user_profiles_table} (
                user_key      STRING,
                energy_target INT,
                diets         STRING,
                allergies     STRING,
                updated_at    TIMESTAMP
            )
            """,
            user_token=user_token,
        )
        _schema_ready = True


# --- in-memory fallback ------------------------------------------------------
_MEM: dict[str, dict] = {}
_MEM_LOCK = threading.Lock()
_logged_backend = False


def _log_backend_once() -> None:
    global _logged_backend
    if not _logged_backend:
        logger.info(
            "profile store backend: %s",
            "warehouse:" + settings.user_profiles_table if _use_warehouse() else "in-memory",
        )
        _logged_backend = True


def _defaults() -> dict:
    return {"energy_target": _DEFAULT_ENERGY_TARGET, "diets": [], "allergies": []}


def _clean(profile: dict) -> dict:
    """Normalize/clamp a profile payload before persisting or returning."""
    try:
        energy = int(profile.get("energy_target", _DEFAULT_ENERGY_TARGET))
    except (TypeError, ValueError):
        energy = _DEFAULT_ENERGY_TARGET
    energy = max(_CAL_MIN, min(_CAL_MAX, energy))
    diets = [str(x) for x in (profile.get("diets") or [])]
    allergies = [str(x) for x in (profile.get("allergies") or [])]
    return {"energy_target": energy, "diets": diets, "allergies": allergies}


# --- public API --------------------------------------------------------------
def get_profile(user_key: str, user_token: str | None = None) -> dict:
    """Return the stored profile for ``user_key``, or sensible defaults."""
    _log_backend_once()
    if not _use_warehouse():
        with _MEM_LOCK:
            stored = _MEM.get(user_key)
            return copy.deepcopy(stored) if stored else _defaults()

    _ensure_schema(user_token)
    rows = warehouse.query(
        f"SELECT energy_target, diets, allergies FROM {settings.user_profiles_table} "
        "WHERE user_key = :user_key",
        params={"user_key": user_key},
        user_token=user_token,
    )
    if not rows:
        return _defaults()
    r = rows[0]
    return {
        "energy_target": r["energy_target"],
        "diets": json.loads(r["diets"]) if r["diets"] else [],
        "allergies": json.loads(r["allergies"]) if r["allergies"] else [],
    }


def upsert_profile(user_key: str, profile: dict, user_token: str | None = None) -> dict:
    """Persist ``profile`` for ``user_key`` and return the cleaned, stored value."""
    _log_backend_once()
    clean = _clean(profile)
    if not _use_warehouse():
        with _MEM_LOCK:
            _MEM[user_key] = copy.deepcopy(clean)
        return clean

    _ensure_schema(user_token)
    warehouse.query(
        f"""
        MERGE INTO {settings.user_profiles_table} t
        USING (SELECT :user_key AS user_key, :energy_target AS energy_target,
                      :diets AS diets, :allergies AS allergies) s
        ON t.user_key = s.user_key
        WHEN MATCHED THEN UPDATE SET
            energy_target = s.energy_target,
            diets         = s.diets,
            allergies     = s.allergies,
            updated_at    = current_timestamp()
        WHEN NOT MATCHED THEN INSERT
            (user_key, energy_target, diets, allergies, updated_at)
            VALUES (s.user_key, s.energy_target, s.diets, s.allergies, current_timestamp())
        """,
        params={
            "user_key": user_key,
            "energy_target": clean["energy_target"],
            "diets": json.dumps(clean["diets"]),
            "allergies": json.dumps(clean["allergies"]),
        },
        user_token=user_token,
    )
    return clean
