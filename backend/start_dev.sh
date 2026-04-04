#!/bin/bash
# Dev startup script that loads .env and overrides any injected env vars
set -a
source /workspace/backend/.env
set +a
cd /workspace/backend
source venv/bin/activate
exec uvicorn app.main:app --reload --port 8000
