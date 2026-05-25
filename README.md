# WarrantyWise: Enterprise Agentic Warranty Replacement Platform

## Executive Overview

WarrantyWise is a portfolio-grade capstone demonstrating a governed, auditable, production-aware agentic AI workflow for customer support warranty replacement. It shows how an enterprise AI architecture can coordinate policy grounding, deterministic guardrails, action control, persistence, auditability, and human review without presenting the system as an unconstrained chatbot.

## Business Problem

Warranty replacement workflows are high-trust support processes. A correct decision requires customer verification, order lookup, warranty policy review, eligibility decisioning, inventory checks, controlled action execution, customer-safe communication, and a durable audit trail. A weak implementation can approve the wrong replacement, cite stale policy, expose unnecessary data, or leave the business unable to reconstruct why a decision was made.

## What the Demo Shows

Primary scenario:

> My laptop screen cracked after 9 months. Can I get a replacement?

Expected behavior:

- Customer identity is verified.
- The order is retrieved and confirmed as delivered.
- The current customer-facing laptop warranty policy is retrieved.
- The cracked screen is identified as excluded accidental damage under the current policy.
- Replacement request creation is blocked by guardrail logic.
- A customer-safe response is generated.
- The workflow state and audit trail are persisted.

## Architecture Summary

```text
Customer UI
→ FastAPI API layer
→ LangGraph workflow
→ governed mock tools
→ deterministic guardrails
→ SQLAlchemy persistence
→ Postgres audit trail
```

FastAPI serves both the API and the static frontend. LangGraph orchestrates the warranty workflow as a stateful graph. Governed tools perform identity verification, order lookup, warranty policy retrieval, eligibility checks, inventory checks, replacement creation, escalation, and customer response generation. SQLAlchemy persists workflow runs, audit events, and human review records.

## Phase 1 Capabilities

- FastAPI backend
- Browser-based demo UI
- LangGraph workflow
- Governed mock tools
- Deterministic eligibility and guardrail logic
- Persisted workflow runs
- Persisted audit events
- Persisted human review records
- Railway deployment support
- Local SQLite fallback
- Railway Postgres compatibility

## Enterprise AI Architecture Concepts Demonstrated

- Agentic workflow orchestration
- State-based control
- Tool/action design
- RAG-style policy grounding using mock policy retrieval
- Deterministic guardrails
- Human handoff simulation
- Auditability and replay
- Data minimization
- Separation of reasoning, decisioning, and action execution
- Cost-aware architecture
- Agentforce-style architecture mapping

## Technology Stack

- Python
- FastAPI
- LangGraph
- SQLAlchemy
- SQLite local fallback
- Railway Postgres
- Vanilla HTML/CSS/JavaScript frontend
- Railway
- GitHub

## Live Demo

Live demo: `<add Railway public URL here>`

## Local Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

The local default database is SQLite:

```env
DATABASE_URL=sqlite:///./warrantywise.db
```

Phase 1 creates tables automatically at startup using SQLAlchemy `Base.metadata.create_all()`. Alembic migrations are a future enhancement.

## API Usage

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Start workflow:

```bash
curl -X POST http://127.0.0.1:8000/api/workflows/start \
  -H "Content-Type: application/json" \
  -d '{
    "customer_request": "My laptop screen cracked after 9 months. Can I get a replacement?",
    "customer_id": "cust_primary_001",
    "order_id": "ord_laptop_001"
  }'
```

Retrieve workflow:

```bash
curl http://127.0.0.1:8000/api/workflows/{workflow_id}
```

Retrieve audit timeline:

```bash
curl http://127.0.0.1:8000/api/workflows/{workflow_id}/audit
```

Submit simulated human review:

```bash
curl -X POST http://127.0.0.1:8000/api/workflows/{workflow_id}/human-review \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "request_more_info",
    "reviewer_id": "reviewer_001",
    "reason": "Need verified customer identity before proceeding."
  }'
```

Retrieve human review records:

```bash
curl http://127.0.0.1:8000/api/workflows/{workflow_id}/human-reviews
```

## Auditability and Governance

WarrantyWise persists workflow state, audit events, and human review decisions. The audit trail helps reconstruct:

- Customer request
- Identity verification
- Order lookup
- Policy retrieval
- Eligibility decision
- Guardrail decision
- Replacement creation or block
- Escalation and human review
- Customer response

Audit payloads are intentionally minimal. The workflow avoids logging full customer profiles, payment data, or unnecessary sensitive fields. This demonstrates enterprise-grade data minimization alongside traceability.

## Cost-Aware Architecture

The current phase is deterministic and does not use real LLM calls. Future cost modeling will include:

- Token consumption
- Tool/API calls
- Retrieved context cost
- Audit/observability overhead
- Human escalation cost
- Prompt caching
- Semantic caching
- Model routing
- State/history summarization
- Execution hard caps

## Agentforce Mapping Preview

- WarrantyWise workflow → Agentforce agent/subagent
- Tools → Agentforce actions
- Warranty policy retrieval → grounding
- Guardrails → Flow/Apex/policy controls
- Human review → case/approval/queue
- Audit events → execution/audit trail

## Current Limitations

- Mock data only
- No real Salesforce integration
- No real customer authentication
- No real shipping/fulfillment integration
- No real LLM call yet
- No real Ragas/Langfuse/LangSmith yet
- No real MCP/A2A yet
- Human review is simulated, not a true LangGraph interrupt/resume yet

## Roadmap

- Polished workflow UI
- Controlled LLM response drafting
- Architecture diagrams
- Screenshots
- Cost model v1
- Audit replay example
- Agentforce mapping
- Ragas evaluation
- Langfuse/LangSmith observability
- CrewAI review crew
- MCP-style tool abstraction
- A2A fulfillment delegation
- LangGraph interrupts for real HITL pause/resume

## Railway Deployment

Railway deployment is designed as one FastAPI app service plus one Railway Postgres service.

1. Create a new Railway project.
2. Add a Postgres service.
3. Add a GitHub repo service connected to this repository.
4. Make sure the app service has `DATABASE_URL` from the Railway Postgres service.
5. Railway provides the `PORT` environment variable automatically.
6. The Docker start command runs Uvicorn on `0.0.0.0:$PORT`.
7. Generate a public domain from the Railway Networking settings.

SQLite is for local development only. Railway should use Postgres through `DATABASE_URL`.

## Repository Structure

```text
backend/app              FastAPI application, database setup, and app entry point
backend/app/workflow     LangGraph state, nodes, graph, and workflow persistence
backend/app/tools        Governed mock tools and synthetic domain data
backend/app/audit        Audit event logging, audit storage, and human review storage
backend/app/models       Pydantic API/domain models and SQLAlchemy ORM models
frontend                 Static HTML/CSS/JavaScript demo UI served by FastAPI
docs                     Architecture, audit, guardrail, cost, and mapping notes
backend/tests            Unit and API tests for workflow, tools, persistence, and serving
```
