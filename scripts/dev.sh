#!/usr/bin/env bash
# Local development: run the FastAPI backend (:8000) and the Vite dev server (:5173).
# The Vite dev server proxies /api -> http://localhost:8000 (see frontend/vite.config.ts),
# so open the app at http://localhost:5173 and let it talk to the backend through the proxy.
set -euo pipefail

# cd to repo root regardless of where the script is invoked from.
cd "$(dirname "$0")/.."

# Local auth + app configuration. Uses the Databricks CLI profile for auth, so no
# raw tokens are exported or stored here.
export DATABRICKS_CONFIG_PROFILE=hackathons
export DATABRICKS_WAREHOUSE_ID=56adb3367ffc45e8
export NUTRITION_CATALOG=flo_heatlh_hackathon
export NUTRITION_SCHEMA=uc5_nutrition_planner
export NUTRITION_TEAM_SCHEMA=team7
export LLM_ENDPOINT=databricks-claude-sonnet-4-6
export RETRIEVAL_MODE=static

# Start the backend in the background and make sure it dies when this script exits.
echo "==> Starting backend (uvicorn app:app) on http://localhost:8000"
(cd src/app && uvicorn app:app --reload --port 8000) &
BACKEND_PID=$!

cleanup() {
  echo "==> Stopping backend (pid ${BACKEND_PID})"
  kill "${BACKEND_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Start the frontend dev server in the foreground (Ctrl-C stops everything).
echo "==> Starting frontend dev server (http://localhost:5173)"
(cd frontend && npm run dev)
