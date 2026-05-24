# warrantywise-agentic-support

WarrantyWise Agentic Support is a local capstone project for a governed warranty replacement workflow. The backend currently exposes a deterministic FastAPI API backed by mocked domain data, governed tools, a local LangGraph workflow, and in-memory audit logging.

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
