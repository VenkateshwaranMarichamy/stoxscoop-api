# StoxScoop API

Production-ready FastAPI backend for tracking structured stock-market events with support for event batches, multiple event types, bulk entry, and market updates.

## Quickstart

### 1) Configure environment

Create `app/.env`:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/stoxscoop
APP_ENV=local
LOG_LEVEL=INFO
APP_PORT=8001
CORS_ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:5174"]
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

### 5) Start PostgreSQL (if not running)

```bash
pg_ctl -D /opt/homebrew/var/postgresql@14 start
```

### 6) Run API

```bash
python -m app.main
```

Swagger docs available at `http://localhost:8001/docs`

---

## API Reference

All endpoints are prefixed with `/api/v1`.

### Batches

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/batches` | Create a new batch |
| `GET` | `/batches` | List all batches (paginated) |
| `GET` | `/batches/{id}` | Get batch with its events |
| `PATCH` | `/batches/{id}/complete` | Mark batch as complete |
| `POST` | `/batches/with-events` | Create batch and events in one call (partial success supported) |

#### `POST /batches/with-events` response

Returns a partial success summary — batch is always created, each event is attempted independently:

```json
{
  "batch": { "id": 10, "batch_name": "Morning News", "..." : "..." },
  "created": 3,
  "failed": 2,
  "results": [
    { "index": 0, "status": "created", "id": 101, "error": null },
    { "index": 1, "status": "failed",  "id": null, "error": "Invalid event_type/event_subtype pair: business/xyz" }
  ]
}
```

---

### Events

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/events` | Create a single event |
| `POST` | `/events/batch` | Bulk insert events into an existing batch |
| `GET` | `/events` | List events with filters |
| `GET` | `/events/{id}` | Get a single event |
| `PATCH` | `/events/{id}` | Partial update an event |
| `DELETE` | `/events/{id}` | Soft delete an event |

#### `GET /events` query params

| Param | Type | Description |
|-------|------|-------------|
| `stock_id` | int | Filter by stock |
| `event_type` | string | e.g. `business`, `disclosure`, `insider` |
| `event_subtype` | string | e.g. `sales_initiative`, `contract_win` |
| `date_from` | date | Inclusive start date |
| `date_to` | date | Inclusive end date |
| `priority` | string | `low`, `medium`, `high` |
| `active_only` | bool | Default `true` |
| `limit` | int | Default 100, max 5000 |
| `offset` | int | Default 0 |

---

### Event Subtypes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/subtypes` | List all event subtypes, optionally filtered by `event_type` |

---

### Market Updates

Generic market news (PLI schemes, inflation, macro events etc.)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/market-updates` | Create a single market update |
| `GET` | `/market-updates` | List market updates with filters |
| `GET` | `/market-updates/{id}` | Get a single market update |
| `PATCH` | `/market-updates/{id}` | Partial update a market update |

#### `GET /market-updates` query params

| Param | Type | Description |
|-------|------|-------------|
| `category` | string | Filter by category |
| `sentiment` | string | Filter by sentiment |
| `impact` | string | Filter by impact |
| `date_from` | datetime | Filter by `published_at >= date_from` |
| `date_to` | datetime | Filter by `published_at <= date_to` |
| `limit` | int | Default 50, max 500 |
| `offset` | int | Default 0 |

---

## Event Types & Detail Fields

Each event type stores additional details in a dedicated table. Pass them in the `detail` object.

| Event Type | Key detail fields |
|------------|-------------------|
| `corporate_action` | `record_date`, `effective_date`, `ratio`, `amount_per_share`, `total_size`, `currency` |
| `disclosure` | `investor_category`, `investor_name`, `transaction_type`, `shares_transacted`, `stake_before`, `stake_after` |
| `insider` | `person_name`, `designation`, `transaction_type`, `shares_transacted`, `stake_before`, `stake_after` |
| `business` | `contract_type`, `client_name`, `contract_value`, `geography`, `campaign_name`, `target_revenue`, `target_timeline`, `product_name`, `target_geography`, `target_segment` |
| `governance` | `person_name`, `designation`, `change_type`, `effective_date`, `reason` |
| `credit_rating` | `agency`, `instrument_type`, `rating_before`, `rating_after`, `outlook_before`, `outlook_after` |
| `financials` | `period_quarter`, `period_year`, `revenue`, `ebitda`, `pat`, `eps`, `beat_miss` |
| `fundraising` | `issue_size`, `price_per_share`, `number_of_shares`, `allottee_name`, `purpose` |
| `legal` | `forum`, `case_number`, `counterparty`, `demand_amount`, `penalty_amount`, `outcome` |

---

## Project Layout

```
app/
  core/         # config, errors, logging
  db/           # session, base
  models/       # SQLAlchemy ORM models
  routes/       # FastAPI routers
  schemas/      # Pydantic request/response schemas
  services/     # business logic
alembic/        # database migrations
```

---

## Troubleshooting

**503 Service Unavailable**
PostgreSQL is not running. Start it with:
```bash
pg_ctl -D /opt/homebrew/var/postgresql@14 start
```
If it fails with `postmaster.pid already exists`, check if the PID belongs to a stale process and remove it:
```bash
rm /opt/homebrew/var/postgresql@14/postmaster.pid
pg_ctl -D /opt/homebrew/var/postgresql@14 start
```
