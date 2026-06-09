#!/usr/bin/env bash
# Build the React/Vite frontend into src/app/static (served by FastAPI at /).
set -euo pipefail

# cd to repo root regardless of where the script is invoked from.
cd "$(dirname "$0")/.."

echo "==> Building frontend into src/app/static"
cd frontend
npm ci
npm run build
echo "==> Frontend build complete"
