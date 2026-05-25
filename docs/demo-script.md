# WarrantyWise Demo Script

This script is for a 5–7 minute walkthrough of the Phase 1 WarrantyWise capstone.

## A. Opening / Positioning

WarrantyWise demonstrates an enterprise-grade agentic workflow for warranty replacement decisions. The problem is not simply answering a customer chat message; the system has to verify identity, retrieve order context, apply the current warranty policy, enforce action guardrails, generate a safe customer response, persist the decision trail, and support human review.

This is a governed warranty replacement workflow. The architecture is designed to show how an enterprise AI architect would separate workflow orchestration, tools, policy grounding, guardrails, persistence, auditability, and human handoff.

## B. Architecture Overview

The Phase 1 architecture is:

```text
Browser UI -> FastAPI -> LangGraph -> governed tools -> guardrails -> SQLAlchemy persistence -> Postgres audit trail
```

FastAPI serves both the API and the static frontend from one Railway app to reduce tool complexity. LangGraph coordinates the stateful workflow. Governed mock tools perform bounded actions like identity verification, order lookup, policy retrieval, eligibility checks, inventory checks, escalation, and response generation. SQLAlchemy persists workflow runs, audit events, and human review records, with Railway Postgres used in deployment and SQLite available locally.

## C. Scenario Setup

Use the primary scenario:

> My laptop screen cracked after 9 months. Can I get a replacement?

This scenario is intentionally tricky. The product is inside the 12-month warranty window, so a shallow system might approve the request. The current warranty policy, however, excludes cracked screens caused by drops, impact, or accidental damage. The correct enterprise behavior is to verify the context, retrieve the current policy, identify the exclusion, block replacement creation, and give the customer a safe explanation.

## D. Live Demo Walkthrough

1. Open the Railway public URL.
2. Click **Load Cracked Screen Scenario**.
3. Click **Run Warranty Workflow**.
4. Point out the workflow result panel.
5. Highlight `eligibility_status = not_eligible`.
6. Highlight `guardrail_decision = block`.
7. Point out that there is no `replacement_request_id`.
8. Read the customer-safe response.
9. Scroll to the audit timeline and show the event sequence.
10. Optionally click **Load Unknown Customer Scenario**, run it, and show escalation plus the human review simulation.

For the cracked-screen scenario, the most important message is that the system does not create a replacement request. It blocks the write/action path because the current policy excludes the issue.

## E. Why This Is Enterprise-Grade

- State-based workflow control keeps the process explainable.
- Tool/action separation makes each operation bounded and testable.
- Eligibility and guardrail logic are deterministic.
- Policy-grounded decisioning uses the current warranty policy, not stale FAQ content.
- Tool outputs use data minimization and avoid exposing unnecessary customer details.
- Audit events are persisted for replay and review.
- Human handoff is simulated for escalation paths.
- Deployment uses Railway with Postgres persistence.
- Tests and documentation cover workflow, API, persistence, auditability, deployment config, and frontend serving.

## F. Key Architecture Decisions

- **Why LangGraph:** It makes the workflow explicit, stateful, and branchable, which is better for governed support workflows than a single free-form chat completion.
- **Why deterministic tools in Phase 1:** The goal is to prove control, auditability, and policy behavior before adding probabilistic LLM behavior.
- **Why no LLM for eligibility:** Eligibility is a business decision that should be deterministic, testable, and policy-controlled.
- **Why the cracked-screen scenario is blocked:** The current policy excludes accidental damage and cracked screens caused by drops, impact, or accidental damage.
- **Why audit events are persisted:** Enterprise reviewers need to reconstruct decisions after the process restarts or after a customer dispute.
- **Why Railway:** It provides a simple deployment path for one FastAPI service and one Postgres service.
- **Why Postgres in deployment:** Workflow results, audit events, and human reviews need durable persistence beyond process memory.

## G. Audit Replay Talking Points

Reference: [docs/audit-replay-example.md](audit-replay-example.md)

The system can reconstruct:

- Customer request
- Identity verification
- Order lookup
- Policy retrieval
- Eligibility decision
- Guardrail decision
- Replacement created, blocked, or escalated
- Customer response

The audit trail shows not only the final outcome, but also which node and tool produced each event, what minimal inputs and outputs were recorded, what policy reference was used, and why the guardrail allowed, blocked, or escalated.

## H. Cost-Aware Architecture Preview

Reference: [docs/cost-model.md](cost-model.md)

Future cost modeling will include:

- LLM token cost
- Tool/API invocation cost
- Retrieved context cost
- Audit/observability overhead
- Human escalation cost
- Semantic caching
- Prompt caching
- Model routing
- State/history summarization
- Execution hard caps

The current deterministic workflow establishes the control plane where those cost decisions can be measured and enforced later.

## I. Future Enhancements

- Polished workflow UI
- Controlled LLM response drafting
- Ragas evaluation
- Langfuse/LangSmith observability
- LangGraph interrupts for true HITL pause/resume
- CrewAI review crew
- MCP tool/resource abstraction
- A2A fulfillment delegation
- Agentforce implementation mapping

## J. 30-Second Version

WarrantyWise is an enterprise agentic AI capstone for warranty replacement support. It uses FastAPI, LangGraph, governed tools, deterministic guardrails, SQLAlchemy persistence, and Railway Postgres to show how a customer request can be verified, policy-grounded, decisioned, audited, and escalated without relying on an uncontrolled chatbot. The primary demo blocks a cracked-screen replacement because the current warranty policy excludes accidental damage, and it persists the full audit trail for replay.

## K. Interview Q&A Prompts

### Why LangGraph?

- It makes workflow state, branching, and tool sequencing explicit.
- It supports future HITL interrupt/resume patterns.
- It is easier to audit than a single opaque agent loop.

### Why no LLM for eligibility?

- Eligibility is a policy decision, not a creative drafting task.
- Deterministic logic is easier to test, audit, and govern.
- LLMs can be added later for controlled response drafting.

### How is auditability handled?

- Each meaningful workflow step emits an `AuditEvent`.
- Events are persisted in the `audit_events` table.
- The UI retrieves events through the audit API and displays the timeline.

### How would this map to Agentforce?

- Workflow -> Agentforce agent or subagent.
- Tools -> Agentforce actions.
- Policy retrieval -> grounding.
- Guardrails -> Flow, Apex, and policy controls.
- Human review -> case, approval, or queue.
- Audit events -> execution and audit trail.

### How would you control cost?

- Track token usage, tool calls, retrieved context, audit overhead, and escalations.
- Add prompt caching, semantic caching, model routing, state summarization, and execution caps.
- Keep deterministic decisions out of LLM calls where possible.

### How would you add real HITL?

- Use LangGraph interrupts for pause/resume.
- Persist checkpoint state.
- Route escalations to a real review queue.
- Resume the graph after a human approval or rejection.

### What would you productionize next?

- Add real identity/order/inventory integrations.
- Add controlled LLM response drafting.
- Add observability and evaluation.
- Add Alembic migrations.
- Add real human review workflow.
- Add Salesforce/Agentforce mapping and integration design.
