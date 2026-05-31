# DecisionTrace AI Phase 1 Release Checklist

## Release Purpose

This checklist validates the Phase 1 portfolio release of DecisionTrace AI, using warranty replacement as the first implemented reference workflow. It is intended for final review before public sharing, interview walkthroughs, or future enhancement work.

Companion release notes: [DecisionTrace AI Phase 1 Release Notes](phase-1-release-notes.md).

## Branding Validation

- [ ] UI header says DecisionTrace AI.
- [ ] Subtitle says Auditable Agentic Workflows for Governed Customer Decisions.
- [ ] Header says Built with LangGraph and OpenAI.
- [ ] README positions DecisionTrace AI as the platform.
- [ ] Warranty replacement is described as the first reference workflow.
- [ ] Screenshots match current branding.
- [ ] Docs consistently distinguish platform name from reference workflow.

## Live Demo Validation

- [ ] Railway public URL loads successfully.
- [ ] `/health` returns status ok.
- [ ] Cracked Screen Scenario runs successfully.
- [ ] Unknown Customer Scenario runs successfully.
- [ ] UI shows real workflow state.
- [ ] UI shows real audit event count.
- [ ] UI shows real tool-call count derived from audit events.
- [ ] UI shows persisted human review records.
- [ ] No fake LLM, cost, latency, Langfuse, or LangSmith metrics are displayed.

## Workflow Validation

- [ ] Cracked-screen scenario returns `eligibility_status = not_eligible`.
- [ ] `guardrail_decision = block`.
- [ ] `replacement_request_id` is not created.
- [ ] Customer response does not claim replacement was created.
- [ ] Unknown customer routes to escalation.
- [ ] Eligible scenario test path still creates replacement when guardrails allow.
- [ ] Deterministic guardrails still control action execution.

## LLM Drafting Validation

- [ ] Without `OPENAI_API_KEY` / `OPENAI_MODEL`, `drafting_status = not_configured`.
- [ ] Without OpenAI config, deterministic fallback response is used.
- [ ] With OpenAI config, `drafting_status = completed`.
- [ ] Model name is shown from real backend response.
- [ ] Token fields are shown only when returned by provider.
- [ ] LLM draft is validated before becoming final response.
- [ ] Unsafe LLM drafts fall back to deterministic response.
- [ ] LLM does not decide eligibility or replacement creation.

## Auditability Validation

- [ ] `workflow_runs` row is created.
- [ ] `audit_events` rows are created.
- [ ] `human_reviews` rows are created when review is submitted.
- [ ] Audit timeline includes `workflow_started` and `workflow_completed`.
- [ ] `policy_retrieved` event includes policy reference.
- [ ] `eligibility_checked` event includes eligibility outcome.
- [ ] `guardrail_decision` event includes block/allow/escalate.
- [ ] Audit replay example matches current behavior.
- [ ] Persisted audit data is retrievable through API.

## Documentation Validation

- [ ] README is up to date.
- [ ] `docs/architecture.md` is up to date.
- [ ] `docs/diagrams.md` renders on GitHub.
- [ ] `docs/demo-script.md` matches live demo behavior.
- [ ] `docs/executive-summary.md` reflects DecisionTrace AI branding.
- [ ] `docs/cost-model.md` reflects current LLM token telemetry and future cost model.
- [ ] `docs/audit-replay-example.md` matches current audit behavior.
- [ ] `docs/agentforce-mapping.md` uses current Agentforce terminology.
- [ ] `docs/phase-1-release-notes.md` summarizes the release scope and telemetry integrity review.
- [ ] `docs/roadmap.md` reflects completed and future work.

## Deployment Validation

- [ ] Railway deployment builds from latest main branch.
- [ ] Railway app service has `DATABASE_URL` configured from Postgres reference variable.
- [ ] Railway app service has `OPENAI_API_KEY` configured only if real LLM drafting is desired.
- [ ] Railway app service has `OPENAI_MODEL` configured only if real LLM drafting is desired.
- [ ] SQLite remains local default.
- [ ] Postgres is used in Railway.
- [ ] Public domain is generated and working.

## Test Validation

Run:

```bash
pytest
node --check frontend/app.js
```

Expected result: all tests pass. The exact test count may change as the project evolves, but Phase 1 should remain green before sharing.

## Known Phase 1 Boundaries

- Mock data only.
- No real Salesforce integration.
- No real customer authentication.
- No real fulfillment integration.
- No natural-language intake classifier yet.
- No multi-turn conversation workflow yet.
- No true LangGraph interrupt/resume yet.
- No Langfuse/LangSmith tracing in Phase 1. LangSmith tracing is a Phase 2 branch capability.
- No Ragas evaluation yet.
- No cost-optimized orchestration yet.
- No CrewAI/MCP/A2A implementation yet.

## Phase 1 Release Decision

Phase 1 is release-ready when the live demo, workflow behavior, LLM drafting boundary, audit replay, documentation, screenshots, and tests are all validated.
