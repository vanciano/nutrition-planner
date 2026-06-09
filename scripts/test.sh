#!/usr/bin/env bash
# Run the test suite. Unit tests always; integration tests only on RUN_INTEGRATION=1.
set -euo pipefail

# cd to repo root regardless of where the script is invoked from.
cd "$(dirname "$0")/.."

# Activate a local virtualenv if one is present.
if [[ -d ".venv" ]]; then
  echo "==> Activating .venv"
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

echo "==> Running unit tests (pytest -m 'not integration')"
pytest -m "not integration" -q

if [[ "${RUN_INTEGRATION:-0}" == "1" ]]; then
  echo "==> Running integration tests (pytest -m integration)"
  pytest -m integration -q
fi

echo "==> Tests complete"
