# Architecture

## Architecture Diagrams

See [DecisionTrace AI Architecture Diagrams](diagrams.md) for Mermaid diagrams covering the system architecture, LangGraph workflow, guardrail decisioning, audit/event flow, Railway deployment, and future-state extensions.

## Platform Positioning

DecisionTrace AI is the broader governed decision workflow platform. The current implementation demonstrates the platform through a warranty replacement reference workflow. The same architecture pattern can support other customer-impacting workflows requiring policy grounding, guardrails, audit replay, human review, and cost-aware orchestration.

At a high level, the Phase 1 architecture is: Browser UI → FastAPI → LangGraph → governed tools → guardrails → SQLAlchemy persistence → Postgres audit trail. FastAPI serves both the static frontend and API routes, while LangGraph coordinates deterministic tool calls and records workflow state, audit events, and human review records.

For a presenter-oriented walkthrough, see the [DecisionTrace AI Demo Script](demo-script.md).

For a concise business and architecture overview, see [DecisionTrace AI Executive Summary](executive-summary.md).

For a replayable example of the cracked-screen decision path, see [DecisionTrace AI Audit Replay Example](audit-replay-example.md).

For a Salesforce-native mapping, see [DecisionTrace AI Agentforce Mapping](agentforce-mapping.md).

For known limitations and future roadmap, see [DecisionTrace AI Known Limitations and Future Roadmap](roadmap.md).

For prompt governance and safe iteration details, see the [DecisionTrace AI Prompt Governance Checklist](prompt-governance-checklist.md) and [DecisionTrace AI Safe Iteration Loop](safe-iteration-loop.md).

## Future Architecture: Router, Observability, and Safe Iteration Loop

DecisionTrace AI currently validates the control model for one reference workflow: warranty replacement. The next architecture evolution is a stateful router layer that interprets natural language input and routes to the correct controlled workflow graph.

The router should not execute business actions directly. It should classify intent, extract required fields, identify missing facts, and route to the appropriate workflow. LangGraph remains the control layer for workflow state, routing, guardrails, and action execution. LLMs can support intake classification and response drafting, but deterministic controls still govern eligibility, approval, escalation, and write/action execution.

```text
Customer Message
→ Stateful Intake Router
→ Required Facts Check
→ Workflow Selection
→ LangGraph Workflow
→ Governed Tools
→ Guardrails
→ Audit / Trace Capture
→ Evaluation / Regression Loop
```

### Trace-to-Evaluation Improvement Loop

Production audit and observability data should not only be used for debugging. Real workflow traces can become evidence for recurring failure patterns, especially when a workflow routes incorrectly, misses an escalation condition, drafts unsafe language, or applies the wrong policy context.

Failures should be converted into regression test cases or evaluation examples. This creates a safe improvement loop:

```text
execution
→ trace/audit capture
→ issue detection
→ evaluation case
→ fix
→ regression validation
→ redeploy
```

**Production failures should become regression tests.**

## Phase 2 Intake Router

The `phase-2/intake-router` branch adds an implemented stateful natural-language intake router in `backend/app/intake/`. The router accepts a freeform customer message plus optional customer and order identifiers, then returns structured routing output.

The router can:

- Classify supported intents: `warranty_replacement_request`, `warranty_policy_question`, and `unknown`.
- Extract basic structured facts such as product type, product issue, and damage type.
- Preserve explicit `customer_id` and `order_id` values passed by the caller.
- Identify missing required facts and produce a next clarification question.
- Route ready warranty replacement requests to `routed_workflow = warranty_replacement`.

The router does not decide eligibility, set guardrail decisions, create replacement requests, claim action approval, or execute business tools. When OpenAI configuration is unavailable, the router uses deterministic fallback classification so local development and tests remain stable. The FastAPI endpoint is `POST /api/intake/route`, and the frontend displays router output before the existing workflow is started.

Phase 2 Natural Language Intake is now the primary UI entry point. Customer and order identifiers are shown as optional workflow context required to start the governed workflow, not as the main user experience. The UI makes the context sent to the router visible, and it does not send optional identifiers during analysis unless the user enables that context.

## Phase 1 LangGraph Workflow

Phase 1 uses LangGraph to model the warranty replacement flow as an explicit local state machine. The graph gives the capstone a clear orchestration layer for sequencing governed tools, branching on deterministic state, and preserving decision fields that can later become audit records.

No real external integrations, interrupts, or deployment concerns are included in this phase. Eligibility, guardrail, and action execution remain deterministic and use controlled tool simulations in `backend/app/tools/warranty_tools.py`.

## Workflow Sequence

The local workflow follows this sequence:

1. Verify the customer identity.
2. Look up the order and confirm the order belongs to the customer.
3. Retrieve the current US laptop warranty policy.
4. Check replacement eligibility under the current policy.
5. If eligible, check inventory availability.
6. Run the replacement creation guardrail.
7. Create a replacement request only when all guardrail conditions pass.
8. Escalate to a human when required.
9. Generate a safe customer response.

For the primary scenario, “My laptop screen cracked after 9 months. Can I get a replacement?”, the workflow determines that accidental damage and cracked screens are excluded by the current policy. It does not create a replacement request.

```mermaid
flowchart TD
    START([START]) --> VerifyIdentity[verify_identity]
    VerifyIdentity --> RouteIdentity{identity_verified?}
    RouteIdentity -- no --> Escalate[escalate_to_human]
    RouteIdentity -- yes --> LookupOrder[lookup_order]

    LookupOrder --> RouteOrder{order retrieved and authorized?}
    RouteOrder -- no --> Escalate
    RouteOrder -- yes --> RetrievePolicy[retrieve_warranty_policy]

    RetrievePolicy --> RoutePolicy{policy_reference present?}
    RoutePolicy -- no --> Escalate
    RoutePolicy -- yes --> CheckEligibility[check_replacement_eligibility]

    CheckEligibility --> RouteEligibility{eligibility_status}
    RouteEligibility -- not_eligible --> Guardrail[guardrail_check]
    RouteEligibility -- unknown or human_review_required --> Escalate
    RouteEligibility -- eligible --> CheckInventory[check_inventory_availability]

    CheckInventory --> Guardrail[guardrail_check]
    Guardrail --> RouteGuardrail{guardrail_decision}
    RouteGuardrail -- allow --> CreateReplacement[create_replacement_request]
    RouteGuardrail -- block --> GenerateResponse
    RouteGuardrail -- escalate --> Escalate

    CreateReplacement --> GenerateResponse
    Escalate --> GenerateResponse
    GenerateResponse --> END([END])
```

## Phase 1 Tooling

All Phase 1 tools are deterministic simulations. They return simple dictionaries, include `result_status`, and apply local guardrails before returning action-oriented results. The workflow does not use the deprecated warranty policy in the happy path; it retrieves only the current policy for decisioning.

Future enhancements include LangGraph interrupts, persistence, observability, Ragas evaluation, CrewAI collaboration patterns, MCP tool integration, and A2A interoperability. Those capabilities are intentionally deferred so the first workflow remains easy to test and explain.

## Controlled LLM Response Drafting

DecisionTrace AI supports controlled LLM response drafting at the end of the workflow when `OPENAI_API_KEY` and `OPENAI_MODEL` are configured. The LLM receives only minimized structured state: customer request, eligibility result, policy reference/version, guardrail decision, replacement/escalation identifiers, escalation reason, and workflow status.

The LLM does not decide identity verification, order lookup, policy outcome, eligibility, guardrail decisions, replacement creation, or escalation. Those remain governed by deterministic LangGraph nodes and controlled tool simulations.

The deterministic `generate_customer_response` tool still runs first. The LLM may draft alternate customer-facing wording, but a deterministic validator must pass before the LLM response becomes the final response. The validator blocks drafts that claim a replacement was created without a `replacement_request_id`, promise eligibility for a `not_eligible` case, imply a blocked action was allowed, invent human escalation, or mention implementation details.

If LLM drafting is disabled, not configured, fails, or fails validation, the workflow keeps the deterministic customer response and records the fallback source in workflow state and audit events.

## Phase 1 Auditability

The workflow records audit events for meaningful steps: workflow start, identity verification, order lookup, policy retrieval, eligibility checks, inventory checks, guardrail decisions, replacement request creation, human escalation, customer response generation, workflow completion, and workflow failure.

Audit logging is persisted through SQLAlchemy in the `audit_events` table. This keeps Phase 1 deterministic and testable while preserving the shape of the audit trail that will later run on Postgres for durable deployment.

## Phase 1 API Layer

FastAPI exposes the local workflow for frontend or external callers. The API does not add LangGraph interrupt/resume behavior.

Endpoints:

- `GET /health`: health check.
- `POST /api/workflows/start`: starts a warranty workflow and stores the final state.
- `GET /api/workflows/{workflow_id}`: retrieves the stored workflow state.
- `GET /api/workflows/{workflow_id}/audit`: retrieves the audit timeline for a stored workflow.
- `POST /api/workflows/{workflow_id}/human-review`: simulates human review metadata for escalated workflows.
- `GET /api/workflows/{workflow_id}/human-reviews`: retrieves persisted human review records.

Workflow results are stored through `backend/app/workflow/store.py`.

## Phase 1 Frontend Demo

The Phase 1 frontend is a lightweight static UI served directly by FastAPI from the `frontend/` directory. It uses vanilla HTML, CSS, and JavaScript, with no React, Vite, Node, npm, or frontend build tooling.

The UI visualizes the local LangGraph workflow by letting a user submit a customer request, view the final decision state, inspect the guardrail result, read the audit timeline, and simulate human review when an escalation exists.

React and Vite can be added later if the UI grows into a richer application. They are intentionally skipped in Phase 1 to reduce tooling complexity and keep the capstone demo focused on backend workflow behavior, governance, and auditability.

## Polished Phase 1 Workflow Console

The Phase 1 frontend has been polished into a simple enterprise workflow console without adding a frontend framework. It remains vanilla HTML, CSS, and JavaScript served by FastAPI, so the deployed architecture stays one app service plus one database.

The console renders only real data from existing backend APIs: workflow state, persisted audit events, derived audit/tool-call counts, escalation state, and persisted human review records. Replacement action status, policy reference, guardrail decision, audit replay rows, and human review status are computed from those API responses instead of fabricated telemetry.

The UI now shows real LLM drafting metadata when present, including drafting status, model name, validation status, response source, and provider-reported token fields. Cost telemetry, Langfuse/LangSmith trace links, latency instrumentation, and Ragas evaluation results should be added only after the backend emits real instrumentation for them. Until then, they are shown only as planned Phase 2 enhancements.

## Phase 1 Persistence Layer

Phase 1 uses synchronous SQLAlchemy with a SQLite local fallback. The default `DATABASE_URL` is `sqlite:///./warrantywise.db`, so local development and tests do not require Postgres.

The persistence tables are:

- `workflow_runs`: stores workflow IDs, correlation IDs, customer/order references, workflow status, and final workflow state as JSON.
- `audit_events`: stores reconstructable workflow audit events with safe input/output summaries.
- `human_reviews`: stores simulated human review decisions for escalated workflows.

The design is compatible with Railway Postgres later by setting `DATABASE_URL` to a `postgresql://...` connection string. Phase 1 uses `Base.metadata.create_all()` at startup instead of Alembic migrations; migrations are a future enhancement.

Persistence improves auditability because workflow decisions, guardrail outcomes, and human review records survive API calls and process restarts. It gives the capstone a durable trail for enterprise review without changing the deterministic workflow behavior.

## Phase 1 Deployment Architecture

The Railway deployment architecture is intentionally simple:

- One Railway project.
- One FastAPI service built from the root Dockerfile.
- One Railway Postgres service.
- FastAPI serves both API routes and the static frontend.
- SQLAlchemy abstracts the local SQLite database and the deployed Postgres database.

The app listens on `0.0.0.0` and uses Railway’s `PORT` environment variable. Railway injects the Postgres `DATABASE_URL`, and the app normalizes standard `postgresql://...` URLs to SQLAlchemy’s psycopg-compatible driver format.

No Vercel, separate frontend service, real LLM service, LangGraph interrupts, or observability stack is added in Phase 1. The deployment shape stays focused on one app container plus one managed database.

## Phase 1 Screenshots

Baseline screenshots are available in `docs/screenshots/phase1/`. These show the deployed Railway demo before the polished UI enhancement step.
