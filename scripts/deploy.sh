#!/usr/bin/env bash
# Pre-deploy gate + deploy of the nutrition-planner Databricks App.
#
# Flow: test -> build frontend -> validate bundle -> deploy bundle -> run app ->
#       (first-deploy bootstrap) grant the app's service principal read access to
#       the sample data -> print the app URL.
set -euo pipefail

# cd to repo root regardless of where the script is invoked from.
cd "$(dirname "$0")/.."

PROFILE="hackathons"
TARGET="dev"
APP_NAME="nutrition-planner-dev"
APP_RESOURCE_KEY="nutrition_planner"
WAREHOUSE_ID="56adb3367ffc45e8"
CATALOG="flo_heatlh_hackathon"
SCHEMA="uc5_nutrition_planner"
TEAM_SCHEMA="team7"

# --- a. pre-deploy gate: tests (abort on failure) --------------------------------
echo "==> [1/7] Running tests"
scripts/test.sh

# --- b. build the frontend -------------------------------------------------------
echo "==> [2/7] Building frontend"
scripts/build.sh

# --- c. validate the bundle ------------------------------------------------------
echo "==> [3/7] Validating bundle"
databricks bundle validate -t "${TARGET}" -p "${PROFILE}"

# --- d. deploy the bundle --------------------------------------------------------
echo "==> [4/7] Deploying bundle"
databricks bundle deploy -t "${TARGET}" -p "${PROFILE}"

# --- e. run (start) the app ------------------------------------------------------
echo "==> [5/7] Running app resource '${APP_RESOURCE_KEY}'"
databricks bundle run "${APP_RESOURCE_KEY}" -t "${TARGET}" -p "${PROFILE}"

# --- f. fetch the app + its service principal ------------------------------------
echo "==> [6/7] Fetching app metadata"
APP_JSON="$(databricks apps get "${APP_NAME}" -p "${PROFILE}" -o json)"

# Parse the service principal id/name. Field naming varies across CLI versions, so
# try the common candidates in order. We need a value usable in GRANT ... TO `<sp>`.
SP="$(python3 - "$APP_JSON" <<'PY'
import json, sys
app = json.loads(sys.argv[1])
candidates = [
    "service_principal_client_id",
    "service_principal_name",
    "service_principal_id",
]
sp = ""
for key in candidates:
    val = app.get(key)
    if val:
        sp = str(val)
        break
print(sp)
PY
)"

APP_URL="$(python3 - "$APP_JSON" <<'PY'
import json, sys
app = json.loads(sys.argv[1])
print(app.get("url", ""))
PY
)"

if [[ -z "${SP}" ]]; then
  echo "WARN: could not determine the app service principal from 'apps get' output." >&2
  echo "WARN: skipping data/endpoint grants. Inspect the JSON below and grant manually:" >&2
  echo "${APP_JSON}" >&2
else
  echo "==> App service principal: ${SP}"

  # =============================================================================
  # FIRST-DEPLOY BOOTSTRAP (safe to re-run).
  # Grants the app's service principal read access to the read-only sample data
  # read-only sample data. All steps are idempotent in
  # effect and non-fatal: re-running after the grants already exist is harmless,
  # and a failure here does not abort the deploy (the app is already running).
  # =============================================================================

  # --- g. grant read on the sample data via the Statement Execution API --------
  echo "==> [7/7] Granting service principal read access to sample data (non-fatal)"
  run_grant() {
    local stmt="$1"
    echo "    GRANT: ${stmt}"
    local payload
    payload="$(python3 - "$WAREHOUSE_ID" "$stmt" <<'PY'
import json, sys
print(json.dumps({
    "warehouse_id": sys.argv[1],
    "statement": sys.argv[2],
    "wait_timeout": "30s",
}))
PY
)"
    if ! databricks api post /api/2.0/sql/statements --json "${payload}" -p "${PROFILE}"; then
      echo "    WARN: grant failed (continuing): ${stmt}" >&2
    fi
  }

  run_grant "GRANT USE CATALOG ON CATALOG ${CATALOG} TO \`${SP}\`"
  run_grant "GRANT USE SCHEMA ON SCHEMA ${CATALOG}.${SCHEMA} TO \`${SP}\`"
  run_grant "GRANT SELECT ON SCHEMA ${CATALOG}.${SCHEMA} TO \`${SP}\`"

  # NOTE: profile reads/writes to ${CATALOG}.${TEAM_SCHEMA}.user_profiles run
  # on-behalf-of the signed-in user (app `sql` user scope), who is in `account users`
  # and already holds USE SCHEMA / CREATE TABLE / SELECT / MODIFY on ${TEAM_SCHEMA}.
  # So the app service principal needs no grant there.
fi

# --- i. print the app URL --------------------------------------------------------
echo "==> Deploy complete"
if [[ -n "${APP_URL}" ]]; then
  echo "==> App URL: ${APP_URL}"
else
  echo "WARN: app URL not found in 'apps get' output." >&2
fi
