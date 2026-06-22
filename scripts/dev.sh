#!/usr/bin/env sh
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
trap 'kill "$BACKEND_PID" 2>/dev/null || true' EXIT
cd "$ROOT/frontend"
npm run dev

