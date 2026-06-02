# DecisionTrace AI API Reference

## Purpose

This document provides a human-readable API reference for DecisionTrace AI Phase 2. FastAPI also provides live interactive API documentation at:

- `/docs`
- `/openapi.json`

For release context and validated Phase 2 scenarios, see [DecisionTrace AI Phase 2 Release Notes](phase-2-release-notes.md).

The APIs are organized around the platform control model:

- Intake APIs collect and validate required facts.
- Workflow APIs execute governed decisions.
- Audit APIs replay what happened.
- Human review APIs capture review decisions.
- Observability APIs report tracing configuration.
- Correlation APIs connect intake, workflow, audit, and traces.
- Monitoring APIs aggregate governed workflow outcomes.

## API Groups

- Health
- Intake Router
- Intake Sessions
- Workflow Execution
- Human Review
- Observability
- Correlation
- Monitoring

## Health

### GET `/health`

Used for deployment and runtime health validation.

Example response:

```json
{
  "status": "ok",
  "service": "warrantywise-agentic-support",
  "version": "0.1.0"
}
```

## Intake Router

### POST `/api/intake/route`

Performs single-turn natural-language intake routing. It classifies intent, extracts customer and order identifiers when present, validates required fields and identifier format, and returns whether the governed workflow can be started.

This endpoint does not start the governed workflow. It does not decide eligibility, guardrails, escalation, replacement creation, or action approval.

Request fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `message` | string | yes | Freeform customer message. |
| `customer_id` | string or null | no | Optional explicit customer identifier. |
| `order_id` | string or null | no | Optional explicit order identifier. |

Response fields:

| Field | Notes |
| --- | --- |
| `intent` | `warranty_replacement_request`, `warranty_policy_question`, or `unknown`. |
| `confidence` | Router confidence when available. |
| `product_type` | Extracted product category when available. |
| `product_issue` | Extracted issue such as cracked screen or power failure. |
| `damage_type` | Extracted damage classification when available. |
| `customer_id` | Extracted or explicitly supplied customer ID. |
| `order_id` | Extracted or explicitly supplied order ID. |
| `requires_order_lookup` | Whether the routed workflow needs order lookup. |
| `requires_policy_lookup` | Whether the routed workflow needs policy lookup. |
| `requires_clarification` | True when required facts are missing or invalid. |
| `missing_fields` | Missing required fields. |
| `invalid_fields` | Fields that failed deterministic format validation. |
| `next_question` | Clarification question when needed. |
| `routed_workflow` | Currently `warranty_replacement` when routeable. |
| `routing_status` | Router status summary. |
| `error_message` | Error detail when routing fails. |
| `can_start_workflow` | True only when the required identifiers are present and valid. |

Example missing-info request:

```bash
curl -X POST http://127.0.0.1:8000/api/intake/route \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My laptop screen cracked after 9 months. Can I get a replacement?",
    "customer_id": null,
    "order_id": null
  }'
```

Representative response:

```json
{
  "intent": "warranty_replacement_request",
  "confidence": 0.86,
  "product_type": "laptop",
  "product_issue": "cracked_screen",
  "damage_type": "accidental_damage",
  "customer_id": null,
  "order_id": null,
  "requires_order_lookup": true,
  "requires_policy_lookup": true,
  "requires_clarification": true,
  "missing_fields": ["customer_id", "order_id"],
  "invalid_fields": [],
  "next_question": "Please provide your customer ID and order ID so I can route this request.",
  "routed_workflow": "warranty_replacement",
  "routing_status": "clarification_required",
  "error_message": null,
  "can_start_workflow": false
}
```

Example complete request:

```bash
curl -X POST http://127.0.0.1:8000/api/intake/route \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My laptop screen cracked after 9 months. Can I get a replacement? Customer ID is cust_primary_001 and order ID is ord_laptop_001."
  }'
```

Representative response:

```json
{
  "intent": "warranty_replacement_request",
  "customer_id": "cust_primary_001",
  "order_id": "ord_laptop_001",
  "requires_clarification": false,
  "missing_fields": [],
  "invalid_fields": [],
  "routed_workflow": "warranty_replacement",
  "routing_status": "ready_to_route",
  "can_start_workflow": true
}
```

## Intake Sessions

Intake session APIs support multi-turn clarification. They preserve the original message, store conversation messages in memory for Phase 2, maintain a shared `correlation_id`, collect missing required facts, and enable workflow start only when required facts are present and valid.

Intake session persistence is in-memory in Phase 2. A future phase can persist intake sessions to the database.

### POST `/api/intake/session/start`

Starts a new intake session and runs the router on the initial message.

Request fields:

| Field | Type | Required |
| --- | --- | --- |
| `message` | string | yes |

Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/intake/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My laptop screen cracked after 9 months. Can I get a replacement?"
  }'
```

Representative response:

```json
{
  "intake_session_id": "intake_...",
  "correlation_id": "corr_...",
  "original_message": "My laptop screen cracked after 9 months. Can I get a replacement?",
  "latest_message": "My laptop screen cracked after 9 months. Can I get a replacement?",
  "intent": "warranty_replacement_request",
  "requires_clarification": true,
  "missing_fields": ["customer_id", "order_id"],
  "invalid_fields": [],
  "next_question": "Please provide your customer ID and order ID so I can route this request.",
  "routed_workflow": "warranty_replacement",
  "can_start_workflow": false,
  "conversation_messages": [
    {
      "role": "user",
      "content": "My laptop screen cracked after 9 months. Can I get a replacement?",
      "timestamp": "2026-06-01T00:00:00Z"
    },
    {
      "role": "router",
      "content": "Please provide your customer ID and order ID so I can route this request.",
      "timestamp": "2026-06-01T00:00:00Z"
    }
  ],
  "created_at": "2026-06-01T00:00:00Z",
  "updated_at": "2026-06-01T00:00:00Z"
}
```

### POST `/api/intake/session/{intake_session_id}/reply`

Adds a follow-up user message to an existing intake session, merges newly extracted facts with known session context, and re-runs deterministic readiness validation.

Request fields:

| Field | Type | Required |
| --- | --- | --- |
| `message` | string | yes |

Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/intake/session/intake_123/reply \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Customer ID is cust_primary_001 and order ID is ord_laptop_001."
  }'
```

Representative response:

```json
{
  "intake_session_id": "intake_123",
  "correlation_id": "corr_...",
  "original_message": "My laptop screen cracked after 9 months. Can I get a replacement?",
  "latest_message": "Customer ID is cust_primary_001 and order ID is ord_laptop_001.",
  "intent": "warranty_replacement_request",
  "customer_id": "cust_primary_001",
  "order_id": "ord_laptop_001",
  "requires_clarification": false,
  "missing_fields": [],
  "invalid_fields": [],
  "routed_workflow": "warranty_replacement",
  "routing_status": "ready_to_route",
  "can_start_workflow": true,
  "conversation_messages": []
}
```

If the session is not found, the endpoint returns `404`.

### GET `/api/intake/session/{intake_session_id}`

Returns the current intake session state.

Example response:

```json
{
  "intake_session_id": "intake_123",
  "correlation_id": "corr_...",
  "original_message": "My laptop screen cracked after 9 months. Can I get a replacement?",
  "latest_message": "Customer ID is cust_primary_001 and order ID is ord_laptop_001.",
  "customer_id": "cust_primary_001",
  "order_id": "ord_laptop_001",
  "can_start_workflow": true,
  "conversation_messages": []
}
```

## Workflow Execution

Workflow APIs start and retrieve governed workflow executions. The workflow uses LangGraph-controlled orchestration and owns identity verification, order lookup, policy retrieval, eligibility, guardrails, replacement request creation, escalation, controlled LLM response drafting, and final state persistence.

### POST `/api/workflows/start`

Starts the governed warranty replacement workflow.

Request fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `customer_request` | string | yes | Original customer request. |
| `customer_id` | string | yes | Customer identifier. |
| `order_id` | string | yes | Order identifier. |
| `correlation_id` | string or null | no | Optional ID from intake session. Direct starts generate one if omitted. |

Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/workflows/start \
  -H "Content-Type: application/json" \
  -d '{
    "customer_request": "My laptop screen cracked after 9 months. Can I get a replacement?",
    "customer_id": "cust_primary_001",
    "order_id": "ord_laptop_001",
    "correlation_id": "corr_demo_001"
  }'
```

Representative response:

```json
{
  "workflow_id": "wf_...",
  "correlation_id": "corr_demo_001",
  "workflow_status": "completed",
  "eligibility_status": "not_eligible",
  "guardrail_decision": "block",
  "replacement_request_id": null,
  "escalation_id": null,
  "customer_response": "Based on the current warranty policy...",
  "llm_drafting_status": "not_configured",
  "llm_model_name": null,
  "llm_validation_status": null,
  "final_response_source": "llm_not_configured_fallback"
}
```

### GET `/api/workflows/{workflow_id}`

Retrieves persisted final workflow state.

Response fields:

| Field | Notes |
| --- | --- |
| `workflow_id` | Workflow run ID. |
| `correlation_id` | Shared correlation ID when available. |
| `state` | Full persisted final state dictionary, including workflow, decision, guardrail, response, and LLM metadata fields. |

If the workflow ID is not found, the endpoint returns `404`.

### GET `/api/workflows/{workflow_id}/audit`

Retrieves persisted audit events for a workflow run.

Response fields:

| Field | Notes |
| --- | --- |
| `workflow_id` | Workflow run ID. |
| `correlation_id` | Shared correlation ID. |
| `events` | Ordered audit events. |

Audit event fields include:

- `event_id`
- `workflow_id`
- `correlation_id`
- `event_type`
- `timestamp`
- `actor`
- `node_name`
- `tool_name`
- `input_summary`
- `output_summary`
- `policy_reference`
- `guardrail_decision`
- `reason`

## Human Review

Human review APIs capture and retrieve review decisions for escalated workflows. Human review records are persisted.

### POST `/api/workflows/{workflow_id}/human-review`

Submits a simulated human review decision for an escalated workflow.

Request fields:

| Field | Type | Required |
| --- | --- | --- |
| `decision` | string | yes |
| `reviewer_id` | string | yes |
| `reason` | string or null | no |

Representative response for an escalated workflow:

```json
{
  "workflow_id": "wf_...",
  "decision": "reject_replacement",
  "reviewer_id": "reviewer_001",
  "status": "completed",
  "message": "Human review simulation completed."
}
```

If the workflow does not require review, the response uses `status = "not_required"` and explains that no human review is currently required.

### GET `/api/workflows/{workflow_id}/human-reviews`

Returns persisted human review records for a workflow.

Representative response:

```json
{
  "workflow_id": "wf_...",
  "reviews": [
    {
      "workflow_id": "wf_...",
      "escalation_id": "esc_...",
      "reviewer_id": "reviewer_001",
      "decision": "reject_replacement",
      "reason": "Manual review completed.",
      "status": "completed",
      "created_at": "2026-06-01T00:00:00"
    }
  ]
}
```

If the workflow ID is not found, the endpoint returns `404`.

## Observability

### GET `/api/observability/status`

Returns LangSmith tracing configuration status. It does not expose API keys and does not create fake trace links.

Response fields:

| Field | Notes |
| --- | --- |
| `provider` | Currently `langsmith`. |
| `tracing_status` | `disabled`, `not_configured`, or `enabled`. |
| `project` | LangSmith project name. Defaults to `decisiontrace-phase2`. |
| `trace_url` | Currently null unless a future backend safely provides real run URLs. |
| `trace_url_supported` | Currently false. |

Representative response:

```json
{
  "provider": "langsmith",
  "tracing_status": "not_configured",
  "project": "decisiontrace-phase2",
  "trace_url": null,
  "trace_url_supported": false
}
```

## Correlation

### GET `/api/correlation/{correlation_id}`

Provides a lightweight joined view across intake, workflow, and audit context. It supports end-to-end traceability by connecting the intake session, workflow run, audit event count, workflow status, and final response source when available.

Representative response:

```json
{
  "correlation_id": "corr_...",
  "intake_session_id": "intake_...",
  "workflow_id": "wf_...",
  "audit_event_count": 11,
  "workflow_status": "completed",
  "final_response_source": "llm_validated"
}
```

If no intake session, workflow state, or audit events exist for the correlation ID, the endpoint returns `404`.

## Monitoring

Monitoring APIs power the DecisionTrace Monitoring Dashboard. They are based on persisted governed workflow runs and complement LangSmith dashboards.

- LangSmith monitors execution traces.
- DecisionTrace monitoring tracks business and control outcomes.

The current monitoring dashboard covers persisted governed workflow runs only. Intake-only outcomes such as `clarification_required` and `invalid_input` are not part of persisted workflow-run monitoring yet because intake sessions are in-memory in Phase 2.

### GET `/api/monitoring/summary`

Returns aggregate KPI fields for persisted workflow runs.

Query parameters:

| Parameter | Type | Notes |
| --- | --- | --- |
| `workflow_type` | string | Optional in the API. The frontend requires selection before displaying KPI values. Current value: `warranty_replacement`. |
| `outcome` | string | Optional workflow outcome filter. |

Response fields:

| Field | Notes |
| --- | --- |
| `total_workflow_runs` | Count of persisted workflow runs in scope. |
| `completed_runs` | Runs with completed workflow status. |
| `failed_runs` | Runs classified as failed. |
| `blocked_count` | Runs blocked by eligibility or guardrail. |
| `escalated_count` | Runs with escalation. |
| `allowed_action_count` | Runs that created a governed action. |
| `replacement_request_count` | Runs with replacement request IDs. |
| `llm_drafting_completed_count` | Runs with completed LLM drafting. |
| `llm_validation_failed_count` | Runs where deterministic LLM validation failed. |
| `total_input_tokens` | Provider-reported input tokens from persisted final state. |
| `total_output_tokens` | Provider-reported output tokens from persisted final state. |
| `total_tokens` | Provider-reported total tokens from persisted final state. |
| `total_audit_events` | Audit events across runs in scope. |
| `total_tool_calls` | Audit events with `tool_name` populated. |
| `workflow_type_breakdown` | Count by workflow type. |
| `outcome_breakdown` | Count by workflow-run outcome. |

### GET `/api/monitoring/runs`

Returns recent persisted workflow runs.

Query parameters:

| Parameter | Type | Notes |
| --- | --- | --- |
| `workflow_type` | string | Optional workflow type filter. |
| `outcome` | string | Optional outcome filter. |
| `correlation_id` | string | Optional correlation filter. |
| `limit` | integer | Optional result limit. The backend clamps the value between 1 and 100. |

Response fields per run:

| Field | Notes |
| --- | --- |
| `workflow_id` | Workflow ID. |
| `correlation_id` | Shared correlation ID. |
| `workflow_type` | Current value: `warranty_replacement`. |
| `workflow_status` | Final workflow status. |
| `outcome` | Derived workflow-run outcome. |
| `eligibility_status` | Final eligibility status. |
| `guardrail_decision` | Final guardrail decision. |
| `escalation_id` | Escalation ID if present. |
| `replacement_request_id` | Replacement request ID if present. |
| `llm_drafting_status` | LLM drafting status if present. |
| `llm_validation_status` | LLM validation status if present. |
| `final_response_source` | Deterministic or LLM response source. |
| `llm_input_tokens` | Provider-reported input tokens if present. |
| `llm_output_tokens` | Provider-reported output tokens if present. |
| `llm_total_tokens` | Provider-reported total tokens if present. |
| `audit_event_count` | Count of persisted audit events for the run. |
| `tool_call_count` | Count of audit events with `tool_name`. |
| `created_at` | Workflow row creation time. |
| `updated_at` | Workflow row update time. |

### GET `/api/monitoring/outcomes`

Returns supported workflow type filters and persisted workflow-run outcome filters.

Current workflow types:

- `warranty_replacement`

Current outcome filter values:

- `blocked`
- `escalated`
- `allowed_action`
- `completed_no_action`
- `failed`

The internal safety outcome `unknown` is exposed only if actual persisted workflow runs produce that outcome. Intake-only outcomes such as `clarification_required` and `invalid_input` are not exposed as workflow-run monitoring outcomes.

## Control Boundaries

- Intake router classifies, extracts, validates format, and routes.
- Intake router does not decide eligibility or execute actions.
- Governed workflow verifies business truth.
- Guardrails decide whether action execution is allowed, blocked, or escalated.
- LLM drafts customer response only after workflow decisions.
- Monitoring APIs report real persisted data only.
- No fake telemetry, fake cost, fake latency, or fake trace links are returned.

## Common Demo API Flows

### A. Missing Info

1. `POST /api/intake/session/start`
2. Router detects missing `customer_id` and `order_id`.
3. Router returns a clarification question.
4. Workflow is not started.

### B. Multi-Turn Clarification

1. `POST /api/intake/session/start`
2. Router asks for required identifiers.
3. `POST /api/intake/session/{intake_session_id}/reply`
4. Reply supplies `cust_primary_001` and `ord_laptop_001`.
5. Session returns `can_start_workflow = true`.

### C. Cracked Screen Block

1. Intake becomes ready with `cust_primary_001` and `ord_laptop_001`.
2. `POST /api/workflows/start`
3. Workflow retrieves identity, order, and policy.
4. Eligibility becomes `not_eligible`.
5. Guardrail decision becomes `block`.
6. No `replacement_request_id` is created.
7. `GET /api/workflows/{workflow_id}/audit` replays the decision path.

### D. Eligible Manufacturing Defect

1. Intake becomes ready with `cust_primary_001` and `ord_laptop_power_001`.
2. `POST /api/workflows/start`
3. Workflow returns `eligibility_status = eligible`.
4. Guardrail decision becomes `allow`.
5. `replacement_request_id` is created.

### E. Monitoring

1. Run one or more governed workflows.
2. `GET /api/monitoring/summary?workflow_type=warranty_replacement`
3. `GET /api/monitoring/runs?workflow_type=warranty_replacement`
4. Select a run and call `GET /api/workflows/{workflow_id}/audit` for drilldown.

## Live API Docs

When running locally:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/openapi.json`

When deployed:

- `https://<railway-url>/docs`
- `https://<railway-url>/openapi.json`
