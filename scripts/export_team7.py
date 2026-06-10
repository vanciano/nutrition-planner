#!/usr/bin/env python3
"""Export the team7 reference tables (schema + data) into the repo for
reproducibility / offline use.

Writes, under data/team7/:
  - schema/<table>.sql  — CREATE TABLE DDL (SHOW CREATE TABLE)
  - <table>.csv         — full table data (paginated across result chunks)

Uses the Databricks SQL Statement Execution REST API via the `databricks` CLI
(profile `hackathons`), which works behind the local proxy. Includes
`user_profiles` (note: holds user emails/prefs — hackathon data).

Usage:  .venv/bin/python scripts/export_team7.py
"""
import csv
import json
import os
import subprocess
import sys

PROFILE = os.environ.get("DATABRICKS_CONFIG_PROFILE", "hackathons")
WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID", "56adb3367ffc45e8")
CATALOG = "flo_heatlh_hackathon"
SCHEMA = "team7"

# All team7 tables (incl. user_profiles — note: contains user emails/prefs).
TABLES = [
    "cycle_meal_plans",
    "daily_nutrition_targets",
    "focus_nutrients_by_phase",
    "np_meal_allergens",
    "np_meal_images",
    "np_meal_images_direct",
    "np_meal_ingredients",
    "np_meal_nutrition",
    "np_nutrition_enriched",
    "nutrition_clean",
    "phase_nutrient_goals",
    "user_profiles",
]

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "team7")


def _api(method, path, payload=None):
    cmd = ["databricks", "api", method.lower(), path, "--profile", PROFILE]
    if payload is not None:
        cmd += ["--json", json.dumps(payload)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"{method} {path} failed: {p.stderr[:300]}")
    return json.loads(p.stdout or "{}")


def run_statement(stmt):
    """Execute a statement and return (columns, rows) following all chunks."""
    d = _api("POST", "/api/2.0/sql/statements", {
        "warehouse_id": WAREHOUSE_ID, "statement": stmt,
        "wait_timeout": "50s", "on_wait_timeout": "CONTINUE", "disposition": "INLINE",
    })
    stmt_id = d.get("statement_id")
    # poll until terminal
    while d.get("status", {}).get("state") in ("PENDING", "RUNNING"):
        d = _api("GET", f"/api/2.0/sql/statements/{stmt_id}")
    state = d.get("status", {}).get("state")
    if state != "SUCCEEDED":
        raise RuntimeError(f"statement {state}: {json.dumps(d.get('status', {}))[:300]}")

    cols = [c["name"] for c in d.get("manifest", {}).get("schema", {}).get("columns", [])]
    rows = []
    res = d.get("result", {})
    rows.extend(res.get("data_array") or [])
    nxt = res.get("next_chunk_index")
    while nxt is not None:
        c = _api("GET", f"/api/2.0/sql/statements/{stmt_id}/result/chunks/{nxt}")
        rows.extend(c.get("data_array") or [])
        nxt = c.get("next_chunk_index")
    return cols, rows


def show_create(table):
    _, rows = run_statement(f"SHOW CREATE TABLE {CATALOG}.{SCHEMA}.{table}")
    return rows[0][0] if rows else ""


def main():
    os.makedirs(os.path.join(OUT_DIR, "schema"), exist_ok=True)
    summary = []
    for t in TABLES:
        ddl = show_create(t)
        with open(os.path.join(OUT_DIR, "schema", f"{t}.sql"), "w") as f:
            f.write(ddl.rstrip() + "\n")

        cols, rows = run_statement(f"SELECT * FROM {CATALOG}.{SCHEMA}.{t}")
        path = os.path.join(OUT_DIR, f"{t}.csv")
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            for r in rows:
                w.writerow(["" if v is None else v for v in r])
        summary.append((t, len(rows)))
        print(f"  {t:28} {len(rows):>6} rows  -> data/team7/{t}.csv")

    print("\nExported:")
    for t, n in summary:
        print(f"  {t}: {n}")


if __name__ == "__main__":
    sys.exit(main())
