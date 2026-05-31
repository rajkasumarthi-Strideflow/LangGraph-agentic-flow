# DecisionTrace AI Phase 1 Release Notes

## Release Summary

Phase 1 establishes DecisionTrace AI as an auditable agentic workflow platform for governed customer decisions, with warranty replacement as the first implemented reference workflow. The release demonstrates how a customer-impacting decision can move through controlled workflow state, governed tools, deterministic guardrails, controlled OpenAI response drafting, persistence, and audit replay.

The Phase 1 implementation is intentionally scoped: it proves the control plane around an AI-assisted workflow before adding broader natural-language intake, external integrations, advanced observability, or multi-agent extensions.

## Implemented Capabilities

- FastAPI backend
- LangGraph workflow orchestration
- Controlled tool simulations
- Deterministic eligibility and guardrail logic
- Controlled OpenAI response drafting
- LLM output validation and deterministic fallback
- SQLAlchemy persistence
- Railway Postgres deployment
- Persisted workflow runs
- Persisted audit events
- Persisted human review records
- Polished vanilla HTML/CSS/JavaScript workflow console
- Audit replay
- Real derived telemetry tiles
- No fake LLM, cost, or Langfuse telemetry

## Validated Demo Scenarios

- Cracked-screen scenario: the workflow returns `eligibility_status = not_eligible`, sets `guardrail_decision = block`, does not create a replacement request, and uses an OpenAI-drafted response when configured and validation passes.
- Unknown customer scenario: the workflow fails identity verification, routes to escalation, and supports human review simulation with persisted review records.

## LLM Drafting Boundary

- The LLM drafts final customer response language only.
- The LLM does not decide eligibility.
- The LLM does not create replacement requests.
- The LLM does not override guardrails.
- The LLM receives minimized structured workflow state.
- A deterministic validator must pass before the LLM response becomes the final customer response.
- If the LLM is unavailable, unconfigured, or unsafe, the deterministic fallback response is used.

## Telemetry Integrity

The workflow console displays telemetry from backend API responses or values derived from those responses. Workflow status, eligibility, guardrail decision, replacement action, policy reference, audit event count, tool-call count, human review status, LLM drafting status, model name, token usage, validation status, and final response source are populated from persisted workflow, audit, and human-review data.

LLM token values are displayed only when returned by provider usage metadata. The frontend does not hardcode token counts, model names, fake cost metrics, fake latency values, or fake Langfuse/LangSmith trace links. Phase 2 telemetry items are clearly labeled as planned and not active.

Note: LangSmith tracing is introduced only on a Phase 2 feature branch. It is not part of the Phase 1 release.

## Auditability

- `workflow_runs` stores the final workflow state.
- `audit_events` stores node, tool, decision, LLM drafting, validation, response, and completion events.
- `human_reviews` stores simulated human review decisions.
- Audit replay reconstructs the decision path from customer request through identity verification, order lookup, policy retrieval, eligibility decision, guardrail decision, replacement block or escalation, LLM drafting boundary, and final customer response.

## Known Phase 1 Boundaries

- Synthetic data only
- No real Salesforce integration
- No real authentication
- No real fulfillment integration
- No natural-language intake classifier yet
- No multi-turn conversation workflow yet
- No true LangGraph interrupt/resume yet
- No Langfuse/LangSmith tracing yet
- No Ragas evaluation yet
- No cost-optimized orchestration yet
- No CrewAI/MCP/A2A implementation yet

## Release Validation Checklist

- Railway demo validated
- DecisionTrace branding validated
- OpenAI response drafting validated
- Guardrail block validated
- No replacement created for cracked-screen scenario
- Telemetry integrity reviewed
- Docs and screenshots updated
- Tests passing

## Next Planned Phase

- Natural language intake classifier
- Multi-turn clarification workflow
- Stateful intake router
- Prompt governance checklist
- Observability-to-evaluation loop
- Production failures become regression tests
- Cost telemetry
- Langfuse/LangSmith tracing
- Ragas evaluation
- True LangGraph interrupts
- CrewAI/MCP/A2A extensions
