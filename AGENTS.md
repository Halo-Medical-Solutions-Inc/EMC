# AGENTS.md

## Cursor Cloud specific instructions

### Architecture

Two-service codebase: **backend** (Python/FastAPI on port 8000) and **frontend** (Next.js on port 3000). No monorepo tooling; each is managed independently. See `README.md` for standard setup/run commands.

### Infrastructure

- **PostgreSQL 16** and **Redis** must be running locally before starting the backend.
- Start PostgreSQL: `sudo pg_ctlcluster 16 main start`
- Start Redis: `sudo redis-server --daemonize yes`
- Local dev database: `ai_receptionist` with user `ai_receptionist` / password `devpassword`.

### Critical: Injected Environment Variables

Cloud Agent VMs may have production secrets injected as environment variables (e.g., `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS`). Since pydantic-settings gives OS env vars priority over `.env` files, these will override `backend/.env`. To run the backend against local infrastructure, use the helper script:

```bash
bash /workspace/backend/start_dev.sh
```

This script sources `backend/.env` via `set -a` before launching uvicorn, overriding any injected secrets. Similarly, when running Alembic migrations or seed scripts, prefix them with the local env override:

```bash
cd /workspace/backend && source venv/bin/activate
set -a && source .env && set +a
alembic upgrade head
python scripts/seed_initial_data.py
```

### Running Services

- **Backend**: `bash /workspace/backend/start_dev.sh` (runs uvicorn with `--reload` on port 8000)
- **Frontend**: `cd /workspace/frontend && npm run dev` (Next.js on port 3000)

### Linting

- **Backend**: `cd /workspace/backend && source venv/bin/activate && black --check app/` (note: codebase has pre-existing formatting diffs)
- **Frontend**: `cd /workspace/frontend && npx eslint` (note: codebase has pre-existing lint warnings/errors)

### Seeding Data

After migrations, run `python scripts/seed_initial_data.py` to create the practice and admin users. Run `python scripts/seed_fake_calls.py` for test call data. Both require the local env override described above.

### Test Login

- Email: `keshav@halohealth.app` / Password: `Keshav2004!` (super admin)
- Email: `mandika@halohealth.app` / Password: `Halohealth2025!` (super admin)

### Frontend Environment

`frontend/.env.local` must contain `NEXT_PUBLIC_API_URL=http://localhost:8000`.
