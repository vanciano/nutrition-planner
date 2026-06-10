#!/usr/bin/env python3
"""Restore the team7 dump (data/team7/) into a target catalog.schema.

Recreates each table from schema/<table>.sql (rewriting the original FQN to the
target) and loads the CSV rows via batched INSERTs through the SQL Statement
Execution REST API. Cells are inserted as string literals and implicitly cast by
the destination column types — fine for this reference data; for very large
tables a Spark/`COPY INTO` load is faster.

Usage:
  .venv/bin/python scripts/restore_team7.py --target my_catalog.my_schema [--tables a,b]
"""
import argparse
import csv
import glob
import json
import os
import subprocess

PROFILE = os.environ.get("DATABRICKS_CONFIG_PROFILE", "hackathons")
WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID", "56adb3367ffc45e8")
SRC_FQN_PREFIX = "flo_heatlh_hackathon.team7."
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "team7")
BATCH = 200


def _api(method, path, payload=None):
    cmd = ["databricks", "api", method.lower(), path, "--profile", PROFILE]
    if payload is not None:
        cmd += ["--json", json.dumps(payload)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"{method} {path} failed: {p.stderr[:300]}")
    return json.loads(p.stdout or "{}")


def run(stmt):
    d = _api("POST", "/api/2.0/sql/statements",
             {"warehouse_id": WAREHOUSE_ID, "statement": stmt, "wait_timeout": "50s", "on_wait_timeout": "CONTINUE"})
    sid = d.get("statement_id")
    while d.get("status", {}).get("state") in ("PENDING", "RUNNING"):
        d = _api("GET", f"/api/2.0/sql/statements/{sid}")
    state = d.get("status", {}).get("state")
    if state != "SUCCEEDED":
        raise RuntimeError(f"statement {state}: {json.dumps(d.get('status', {}))[:300]}")
    return d


def _lit(v):
    if v == "":
        return "NULL"
    return "'" + v.replace("'", "''") + "'"


def restore_table(table, target):
    ddl_path = os.path.join(DATA_DIR, "schema", f"{table}.sql")
    csv_path = os.path.join(DATA_DIR, f"{table}.csv")
    with open(ddl_path) as f:
        ddl = f.read().replace(SRC_FQN_PREFIX, target + ".")
    run(f"CREATE SCHEMA IF NOT EXISTS {target}")
    run(ddl)

    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        cols = next(reader)
        collist = ", ".join(f"`{c}`" for c in cols)
        batch, n = [], 0
        for row in reader:
            batch.append("(" + ", ".join(_lit(v) for v in row) + ")")
            if len(batch) >= BATCH:
                run(f"INSERT INTO {target}.{table} ({collist}) VALUES " + ", ".join(batch))
                n += len(batch); batch = []
        if batch:
            run(f"INSERT INTO {target}.{table} ({collist}) VALUES " + ", ".join(batch))
            n += len(batch)
    print(f"  {table}: {n} rows")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="flo_heatlh_hackathon.team7", help="catalog.schema to restore into")
    ap.add_argument("--tables", default="", help="comma-separated subset (default: all)")
    args = ap.parse_args()

    all_tables = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(DATA_DIR, "*.csv")))
    tables = args.tables.split(",") if args.tables else all_tables
    print(f"Restoring into {args.target}:")
    for t in tables:
        restore_table(t.strip(), args.target)


if __name__ == "__main__":
    main()
