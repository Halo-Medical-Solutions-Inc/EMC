# AI Receptionist

AI-powered medical receptionist for handling inbound calls via Twilio + VAPI.

## Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL
- Redis

## Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Fill in your credentials
alembic upgrade head
python scripts/seed_initial_data.py
uvicorn app.main:app --reload
```

## Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Configuration

### Required Services

- **PostgreSQL**: Database for calls, users, sessions, invitations, audit logs
- **Redis**: Pub/sub for real-time websocket updates
- **Twilio**: Inbound call handling
- **VAPI**: AI voice agent for call conversations
- **Claude API**: Post-call data extraction
- **SMTP (Gmail)**: Email invitations and password resets

### Customization

1. Update `backend/app/services/extraction_schema.py` with your provider names
2. Update `backend/.env` with your practice's `FROM_NAME`
3. Run `python scripts/seed_initial_data.py` to create practice + admin user

## Database Migrations

```bash
cd backend
alembic upgrade head
```

## Scripts

| Script | Purpose |
|--------|---------|
| `seed_initial_data.py` | Create practice + first admin user |
| `seed_fake_calls.py` | Generate test call data |
| `count_calls.py` | Display call statistics |
| `inspect_call.py` | View details of a specific call |
| `send_bulk_invitations.py` | Invite multiple users |
| `backfill_display_data.py` | Rebuild display_data for existing calls |
