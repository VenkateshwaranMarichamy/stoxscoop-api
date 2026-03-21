# StoxScoop API

Production-ready FastAPI backend for tracking structured stock-market events with support for event batches, multiple event types, and bulk entry.

## Quickstart

### 1) Configure environment

Create `.env`:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/stoxscoop
APP_ENV=local
LOG_LEVEL=INFO
```

### 2) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Run migrations

```bash
alembic upgrade head
```

### 4) Seed sample data (optional)

```bash
python -m app.seed
```

### 5) Run API

```bash
uvicorn app.main:app --reload
```

Swagger docs are available at `/docs`.

## API

- `POST /batches`
- `GET /batches`
- `GET /stocks`
- `GET /stocks/all`
- `POST /events` (single)
- `POST /events/batch` (bulk insert)
- `GET /events` (filters)
- `GET /events/{id}`

## Project layout

```
app/
  core/
  db/
  models/
  routes/
  schemas/
  services/
```
