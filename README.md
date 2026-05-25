# warrantywise-agentic-support

WarrantyWise Agentic Support is a local capstone project for a governed warranty replacement workflow. The backend currently exposes a deterministic FastAPI API backed by mocked domain data, governed tools, a local LangGraph workflow, and SQLAlchemy persistence.

## Run Local Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

## Test Health

```bash
curl http://localhost:8000/health
```

## Start Workflow

```bash
curl -X POST http://localhost:8000/api/workflows/start \
  -H "Content-Type: application/json" \
  -d '{
    "customer_request": "My laptop screen cracked after 9 months. Can I get a replacement?",
    "customer_id": "cust_primary_001",
    "order_id": "ord_laptop_001"
  }'
```

## Retrieve Workflow

Replace `{workflow_id}` with the ID returned by the start workflow response.

```bash
curl http://localhost:8000/api/workflows/{workflow_id}
```

## Retrieve Audit Timeline

```bash
curl http://localhost:8000/api/workflows/{workflow_id}/audit
```

## Frontend Demo

Run the local backend:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000
```

The Phase 1 UI demonstrates the customer request, workflow result, guardrail decision, audit timeline, and human review simulation using the existing FastAPI workflow endpoints.

## Database Persistence

The local default database is SQLite:

```env
DATABASE_URL=sqlite:///./warrantywise.db
```

Run locally as usual:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Workflow results, audit events, and human review decisions are persisted with SQLAlchemy. Phase 1 creates tables automatically at startup with `Base.metadata.create_all()`, so no local Postgres instance is required.

The persistence layer is compatible with Railway-style Postgres URLs for a later deployment phase:

```env
DATABASE_URL=postgresql://user:password@host:port/dbname
```

Alembic migrations are a future enhancement.

## Railway Deployment

Railway deployment is designed as one FastAPI app service plus one Railway Postgres service.

1. Create a new Railway project.
2. Add a Postgres service.
3. Add a GitHub repo service connected to this repository.
4. Make sure the app service has `DATABASE_URL` from the Railway Postgres service.
5. Railway provides the `PORT` environment variable automatically.
6. The Docker start command runs Uvicorn on `0.0.0.0:$PORT`.
7. Generate a public domain from the Railway Networking settings.

The app uses Dockerfile-based deployment. FastAPI serves both the API and the static frontend, so no Vercel or separate frontend service is needed for Phase 1.

SQLite is for local development only. Railway should use Postgres through `DATABASE_URL`.
