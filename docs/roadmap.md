# DecisionTrace AI Known Limitations and Future Roadmap

## Purpose

This document clarifies Phase 1 boundaries and defines the DecisionTrace AI roadmap for UI polish, controlled LLM use, stateful routing, prompt governance, observability-to-evaluation loops, cost telemetry, true HITL, CrewAI, MCP, A2A, Agentforce implementation mapping, and future domain expansion.

Phase 1 intentionally establishes a governed workflow foundation through the warranty replacement reference workflow before expanding to additional domains or advanced multi-agent protocols.

Before sharing or demoing Phase 1, use the [DecisionTrace AI Phase 1 Release Checklist](phase-1-release-checklist.md) to validate branding, live demo behavior, workflow outcomes, LLM drafting boundaries, auditability, documentation, deployment, and tests.

## Phase 1 Completed Scope

- Deterministic LangGraph workflow
- Controlled tool simulations
- FastAPI backend
- Polished static browser workflow console served by FastAPI
- Railway deployment
- SQLAlchemy persistence
- Railway Postgres compatibility
- Persisted workflow runs
- Persisted audit events
- Persisted human review records
- Human review simulation
- Baseline screenshots
- Architecture diagrams
- Executive summary
- Demo script
- Cost model v1
- Audit replay example
- Agentforce mapping
- Phase 1 release checklist

## Known Phase 1 Limitations

- Synthetic data only
- No real Salesforce integration
- No real customer authentication
- No real order, inventory, shipping, or fulfillment systems
- No LLM intake classifier or multi-turn LLM conversation yet
- No natural language intent classifier yet
- No true LangGraph interrupt/resume yet
- Human review is simulated through API state update
- No Ragas evaluation yet
- No Langfuse/LangSmith observability yet
- No real cost telemetry yet
- No CrewAI implementation yet
- No MCP server implementation yet
- No A2A fulfillment delegation yet
- No production-grade security hardening yet
- No Alembic database migrations yet
- No CI/CD pipeline yet

## Phase 2 Roadmap — Experience, LLM Boundaries, Telemetry, and Evaluation

### Polished Workflow UI

Status: completed for the Phase 1 data surface.

The UI has evolved from a functional prototype into a simple enterprise workflow operations console. It does not use React, Vite, Node, npm, or a frontend framework. It renders real workflow, audit, and human review data from existing backend APIs.

Implemented UI sections:

- Header with app name, environment, and architecture badges
- Request panel
- Natural language warranty question input
- Scenario shortcut buttons
- Decision summary panel
- Workflow timeline
- Audit replay panel
- Real telemetry tiles derived from workflow/audit/review APIs
- Human review panel
- Planned Phase 2 telemetry section

Implemented tile examples:

- Workflow Status
- Eligibility
- Guardrail Decision
- Replacement Action
- Policy Used
- Audit Events
- Tool Calls
- Human Review

The UI shows LLM drafting status and provider-reported token fields when available. It intentionally does not show active dollar cost, latency, or tracing metrics yet because those backend telemetry sources are not implemented.

Future telemetry tile examples:

- Estimated Cost
- LLM Tokens
- Latency
- Trace Status

### Stateful Natural Language Intake Router

Replace the simpler idea of intent classification with a stateful natural language intake router. The router interprets user messages, classifies intent, extracts structured facts, identifies missing information, and routes to the right controlled workflow.

Examples:

- “My laptop screen cracked after 9 months. Is it covered?”
- “My laptop stopped powering on after 6 months. Can I get a replacement?”
- “What does my warranty cover?”

Architecture principle: the intake router is the language layer; LangGraph remains the control layer.

The router may ask for clarification in future multi-turn flows. It may classify intent and extract structured fields, but it must not decide eligibility, approve requests, or execute business actions.

Example structured output:

```json
{
  "intent": "warranty_replacement_request",
  "product_issue": "cracked_screen",
  "damage_type": "possible_accidental_damage",
  "confidence": 0.91,
  "requires_order_lookup": true,
  "requires_policy_lookup": true,
  "requires_clarification": false
}
```

### Prompt Governance Checklist

As LLM usage expands, prompt quality becomes a control risk. Prompts should be treated as governed workflow assets, not informal strings embedded in code.

Future prompt governance should include:

- Scope
- Out-of-scope boundaries
- Allowed actions
- Prohibited claims
- Required output schema
- Escalation conditions
- Entry/exit criteria
- Prompt injection considerations
- Contradiction checks
- Validation rules
- Test coverage

See the [DecisionTrace AI Prompt Governance Checklist](prompt-governance-checklist.md).

### Controlled LLM Response Drafting

Status: implemented for final customer response drafting when OpenAI credentials and a model are configured.

LLM use is limited to customer-safe response drafting, not eligibility decisioning.

Inputs:

- Structured workflow state
- Policy reference
- Eligibility result
- Guardrail decision

Output:

- Customer-safe response

Validation:

- Must not claim replacement was created unless `replacement_request_id` exists.
- Must pass deterministic output validation before replacing the deterministic response.
- Falls back to deterministic response when LLM drafting is disabled, not configured, fails, or fails validation.

### True HITL with LangGraph Interrupts

Replace simulated human review with true LangGraph interrupt/resume.

Include:

- Interrupt for manager approval
- Interrupt for customer confirmation
- Checkpointed state
- Resume with human decision
- Audit human decision and resume result

### Cost Telemetry

Move cost model from documentation into workflow telemetry.

Tracked values:

- `tool_call_count`
- `audit_event_count`
- `human_review_required`
- `estimated_human_review_cost`
- `llm_input_tokens` when provider usage metadata is available
- `llm_output_tokens` when provider usage metadata is available
- `cached_tokens` when provider usage metadata is available
- `estimated_total_cost`

### Observability with Langfuse or LangSmith

Add trace-level observability later.

Include:

- Workflow trace
- Model call trace
- Tool call spans
- Retrieval spans
- Latency
- Token usage
- Cost
- Errors
- Trace link from UI

### Observability-to-Improvement Loop

Trace and audit data should feed evaluation and regression testing. Recurring failures should become evaluator cases, so observability becomes continuous improvement rather than passive logging.

Future workflow:

```text
execution
→ trace/audit capture
→ issue detection
→ evaluator or regression case
→ fix
→ validation
→ controlled redeployment
```

Core principle: production failures should become regression tests.

### Ragas Evaluation Foundation

Add golden test cases and RAG/response evaluation.

Include:

- Context precision
- Context recall
- Faithfulness
- Answer relevance
- Citation/source accuracy
- Policy-grounding checks

## Phase 3 Roadmap — Cost-Optimized and Multi-Agent Architecture

### Self-Serve Workflow Configuration

Longer-term, DecisionTrace AI could become an accelerator where domain teams configure workflow variants using governed templates. Domain users should not get unrestricted control over prompts, tools, routing, or action execution.

Configuration should be constrained by:

- Workflow templates
- Action catalogs
- Variable/state definitions
- Prompt quality checks
- Guardrail requirements
- Evaluation gates
- Approval workflow
- Deployment controls

### Safe Iteration Operating Model

Enterprises need a way to iterate on AI workflows safely. DecisionTrace AI’s future operating model should support:

- Domain team proposes workflow or prompt change
- Validation checks run
- Offline evals run
- Audit/risk review occurs when needed
- Controlled deployment proceeds
- Production traces are monitored
- Failures are converted into regression tests

See the [DecisionTrace AI Safe Iteration Loop](safe-iteration-loop.md).

### Cost-Optimized Orchestration

Phase 2 observes cost. Phase 3 uses cost signals to control orchestration.

Include:

- Dynamic model routing
- Prompt caching
- Semantic caching
- State/history summarization
- Retrieved chunk limits
- Tool-call caps
- Retry caps
- Cost-aware escalation

### Dynamic Model Routing

Use low-cost models for simple classification, formatting, and summarization. Use frontier models for high-risk, ambiguous, policy-impacting, or high-value cases.

Criteria:

- Task complexity
- Risk tier
- Ambiguity
- Policy impact
- Tool/action risk
- Confidence score
- Failure/retry signals
- Customer/business value
- Regulatory sensitivity
- Nuanced communication needs

### CrewAI Review Crew

Add a bounded CrewAI team for complex warranty review.

Possible agents:

- Order Context Analyst
- Warranty Policy Specialist
- Replacement Eligibility Analyst
- Risk Classifier
- Customer Response Drafter
- Compliance and Output Validator

CrewAI should return a structured recommendation, while LangGraph keeps workflow control, guardrails, approvals, and execution.

### MCP Tool and Resource Abstraction

Expose tools/resources/prompts through MCP later.

Include:

- `lookup_order`
- `retrieve_warranty_policy`
- `check_replacement_eligibility`
- `check_inventory_availability`
- `create_case`
- Warranty policy resources
- Response drafting prompts

### A2A Fulfillment Delegation

Add A2A for cross-agent delegation to an external Fulfillment Agent after replacement eligibility is approved.

Include:

- Warranty Agent owns eligibility
- Fulfillment Agent owns shipment execution
- Send minimal structured context
- Return shipment artifact
- Log correlation ID on both sides

### Agentforce Implementation Path

Move from conceptual mapping to a Salesforce-native implementation path using:

- Agentforce Agent
- Agent Script
- Subagents
- Variables
- Actions
- Available-when filters
- Flow/Apex
- Knowledge/Data Cloud grounding
- Case/queue/approval handoff
- Agentforce DX

### Domain Expansion

DecisionTrace AI can extend the same governed workflow pattern beyond warranty replacement into additional customer-impacting domains:

- Credit approval
- Insurance claims
- Refund governance
- Subscription cancellation
- Compliance exception review

## Future Polished UI Draft

Header:

- DecisionTrace AI
- Auditable Agentic Workflows for Governed Customer Decisions
- Badges: Phase 2, LangGraph, Auditable, Cost-Aware

Main layout:

- Request Panel
- Decision Summary
- Workflow Timeline
- Telemetry Tiles
- Audit Replay
- Human Review

Tile row:

- Audit Events
- Tool Calls
- Estimated Cost
- Human Review
- LLM Tokens
- Trace Status

Observability, audit, and cost telemetry should be neatly arranged as tiles so an operator can understand workflow status without reading raw logs.

## Roadmap Summary Table

| Phase | Theme | Key Enhancements | Outcome |
| --- | --- | --- | --- |
| Phase 1 | Governed workflow foundation | Warranty replacement reference workflow, LangGraph workflow, controlled tool simulations, audit persistence, Railway deployment, screenshots, docs | Demonstrates deterministic enterprise control plane. |
| Phase 2 | LLM boundaries, router, telemetry, evaluation | Stateful intake router, prompt governance, controlled LLM drafting, LangGraph interrupts, cost telemetry, observability, Ragas, domain expansion planning | Makes DecisionTrace AI more measurable, evaluation-ready, and production-aware. |
| Phase 3 | Safe iteration, cost optimization, multi-agent, MCP/A2A, Agentforce path | Self-serve workflow configuration, safe iteration gates, model routing, caching, CrewAI review crew, MCP abstraction, A2A delegation, Agentforce implementation, additional governed decision workflows | Evolves into a cost-aware, extensible enterprise agent architecture. |

## Architecture Principle

Enterprise agentic AI should evolve in layers: first establish governed workflow control, then add LLM reasoning in bounded places, then add observability and evaluation, then optimize cost and introduce multi-agent/protocol extensions.
