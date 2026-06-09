#!/usr/bin/env python3
"""OPT-IN one-time RAG index builder for the nutrition-planner app.

==============================================================================
THIS IS NOT PART OF THE NORMAL DEPLOY (scripts/deploy.sh does NOT call this).
==============================================================================

The default app runs with RETRIEVAL_MODE=static and needs zero extra infra.
This script is the opt-in "scale-up" path: it builds a Databricks Vector Search
Delta Sync index so the app can run with RETRIEVAL_MODE=vector.

Run it once (manually) when you want vector retrieval:

    DATABRICKS_CONFIG_PROFILE=hackathons python3 scripts/index_build.py

WARNING: provisioning a Vector Search endpoint takes several MINUTES the first
time. This script waits for the endpoint to come ONLINE before creating the
index, so expect it to block for a while. It is safe to re-run: every step
catches "already exists" and continues.

What it does:
  1. Create/refresh a source Delta table flo_heatlh_hackathon.team7.meals from the
     read-only sample table cycle_meal_plans, with a `text` column for embeddings
     and Change Data Feed enabled (required for Delta Sync indexes).
  2. Ensure a Vector Search endpoint exists and is ONLINE.
  3. Create a TRIGGERED Delta Sync index flo_heatlh_hackathon.team7.meals_idx that
     embeds `text` via the databricks-gte-large-en embedding endpoint.
  4. Print the VECTOR_ENDPOINT / VECTOR_INDEX values to set in src/app/app.yaml.

Dependencies (install into your venv if missing):
    pip install databricks-sdk databricks-vectorsearch
"""
from __future__ import annotations

import os
import sys
import time

# --- configuration (kept in sync with src/app/app.yaml) ----------------------
CATALOG = "flo_heatlh_hackathon"
READ_SCHEMA = "uc5_nutrition_planner"     # read-only sample source
TEAM_SCHEMA = "team7"                     # our write schema
WAREHOUSE_ID = "56adb3367ffc45e8"

SOURCE_VIEW_TABLE = f"{CATALOG}.{READ_SCHEMA}.cycle_meal_plans"
MEALS_TABLE = f"{CATALOG}.{TEAM_SCHEMA}.meals"          # Delta source for the index
INDEX_NAME = f"{CATALOG}.{TEAM_SCHEMA}.meals_idx"       # Delta Sync index

VECTOR_ENDPOINT = "nutrition-vs"
EMBEDDING_ENDPOINT = "databricks-gte-large-en"
PRIMARY_KEY = "meal_id"
EMBEDDING_SOURCE_COLUMN = "text"

# how long to wait for the VS endpoint to come ONLINE
ENDPOINT_WAIT_TIMEOUT_S = 45 * 60
ENDPOINT_POLL_INTERVAL_S = 30


def _log(msg: str) -> None:
    print(f"[index_build] {msg}", flush=True)


def _fatal(msg: str, exc: Exception | None = None) -> "None":
    print(f"[index_build] ERROR: {msg}", file=sys.stderr, flush=True)
    if exc is not None:
        print(f"[index_build] cause: {exc!r}", file=sys.stderr, flush=True)
    sys.exit(1)


def _is_already_exists(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(s in text for s in ("already exists", "alreadyexists", "resource_conflict", "conflict"))


# -----------------------------------------------------------------------------
# Step 1: build the source Delta table via the Statement Execution API.
# -----------------------------------------------------------------------------
def build_source_table(w) -> None:
    _log(f"Step 1: building source Delta table {MEALS_TABLE} from {SOURCE_VIEW_TABLE}")
    statement = f"""
        CREATE OR REPLACE TABLE {MEALS_TABLE}
        TBLPROPERTIES (delta.enableChangeDataFeed = true)
        AS SELECT
            meal_id,
            cycle_phase,
            meal_name,
            description,
            key_nutrients,
            concat_ws(' ', meal_name, description, key_nutrients) AS text
        FROM {SOURCE_VIEW_TABLE}
    """.strip()

    try:
        resp = w.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID,
            statement=statement,
            wait_timeout="50s",
        )
        state = getattr(getattr(resp, "status", None), "state", None)
        _log(f"  statement state: {state}")
        # If the warehouse was cold the statement may still be PENDING/RUNNING.
        if state and str(state).upper() not in ("SUCCEEDED", "PENDING", "RUNNING"):
            err = getattr(getattr(resp, "status", None), "error", None)
            _log(f"  WARN: statement did not succeed immediately: {err}")
        _log("  source table ready (CREATE OR REPLACE is itself idempotent)")
    except Exception as exc:  # noqa: BLE001
        _fatal(
            "failed to create the source Delta table. Check that the warehouse is "
            f"running and you have CREATE on {CATALOG}.{TEAM_SCHEMA}.",
            exc,
        )


# -----------------------------------------------------------------------------
# Step 2: ensure the Vector Search endpoint exists and is ONLINE.
# -----------------------------------------------------------------------------
def ensure_endpoint(vsc) -> None:
    _log(f"Step 2: ensuring Vector Search endpoint '{VECTOR_ENDPOINT}' exists")
    try:
        vsc.create_endpoint(name=VECTOR_ENDPOINT, endpoint_type="STANDARD")
        _log("  create_endpoint requested (provisioning can take several minutes)")
    except Exception as exc:  # noqa: BLE001
        if _is_already_exists(exc):
            _log("  endpoint already exists, continuing")
        else:
            _fatal("failed to create the Vector Search endpoint.", exc)

    _log("  waiting for endpoint to become ONLINE (this can take MINUTES)...")
    deadline = time.time() + ENDPOINT_WAIT_TIMEOUT_S
    while time.time() < deadline:
        try:
            ep = vsc.get_endpoint(VECTOR_ENDPOINT)
        except Exception as exc:  # noqa: BLE001
            _log(f"  get_endpoint failed transiently ({exc!r}); retrying...")
            time.sleep(ENDPOINT_POLL_INTERVAL_S)
            continue

        state = ""
        if isinstance(ep, dict):
            state = (ep.get("endpoint_status", {}) or {}).get("state", "") or ep.get("state", "")
        state = str(state).upper()
        _log(f"  endpoint state: {state or '<unknown>'}")
        if state == "ONLINE":
            _log("  endpoint is ONLINE")
            return
        if state in ("OFFLINE", "FAILED", "ENDPOINT_STATE_FAILED"):
            _fatal(f"endpoint entered a terminal non-online state: {state}")
        time.sleep(ENDPOINT_POLL_INTERVAL_S)

    _fatal(
        f"timed out after {ENDPOINT_WAIT_TIMEOUT_S}s waiting for endpoint "
        f"'{VECTOR_ENDPOINT}' to come ONLINE. Re-run this script later; it is "
        "safe to re-run and will pick up where it left off."
    )


# -----------------------------------------------------------------------------
# Step 3: create the Delta Sync index.
# -----------------------------------------------------------------------------
def ensure_index(vsc) -> None:
    _log(f"Step 3: creating Delta Sync index '{INDEX_NAME}'")
    try:
        vsc.create_delta_sync_index(
            endpoint_name=VECTOR_ENDPOINT,
            index_name=INDEX_NAME,
            source_table_name=MEALS_TABLE,
            pipeline_type="TRIGGERED",
            primary_key=PRIMARY_KEY,
            embedding_source_column=EMBEDDING_SOURCE_COLUMN,
            embedding_model_endpoint_name=EMBEDDING_ENDPOINT,
        )
        _log("  index creation requested (initial sync runs in the background)")
    except Exception as exc:  # noqa: BLE001
        if _is_already_exists(exc):
            _log("  index already exists, continuing")
        else:
            _fatal("failed to create the Delta Sync index.", exc)


def main() -> None:
    # Lazy imports so a missing dependency yields a clear, actionable message.
    try:
        from databricks.sdk import WorkspaceClient
    except Exception as exc:  # noqa: BLE001
        _fatal("databricks-sdk is not installed. Run: pip install databricks-sdk", exc)

    try:
        from databricks.vector_search.client import VectorSearchClient
    except Exception as exc:  # noqa: BLE001
        _fatal(
            "databricks-vectorsearch is not installed. "
            "Run: pip install databricks-vectorsearch",
            exc,
        )

    if not os.environ.get("DATABRICKS_CONFIG_PROFILE"):
        _log("DATABRICKS_CONFIG_PROFILE not set; relying on default SDK auth resolution.")
        _log("Tip: DATABRICKS_CONFIG_PROFILE=hackathons python3 scripts/index_build.py")

    # WorkspaceClient picks up auth from env / profile automatically.
    w = WorkspaceClient()
    vsc = VectorSearchClient(disable_notice=True)

    build_source_table(w)
    ensure_endpoint(vsc)
    ensure_index(vsc)

    _log("Done. Set these in src/app/app.yaml (and flip RETRIEVAL_MODE to 'vector'):")
    print()
    print(f"  VECTOR_ENDPOINT={VECTOR_ENDPOINT}")
    print(f"  VECTOR_INDEX={INDEX_NAME}")
    print()
    _log("Then redeploy with scripts/deploy.sh.")


if __name__ == "__main__":
    main()
