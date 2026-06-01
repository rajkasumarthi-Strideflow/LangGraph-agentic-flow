# DecisionTrace AI Phase 2 Validation Checklist

## Purpose

This checklist validates the Phase 2 development branch before merging into the stable `main` branch or creating a Phase 2 release.

## Branch and Deployment Validation

- [ ] Current branch is `phase-2/intake-router`
- [ ] Phase 1 remains stable on `main`
- [ ] Phase 1 release tag `v1.0-phase-1` remains unchanged
- [ ] Phase 2 Railway service deploys from `phase-2/intake-router`
- [ ] Phase 2 Railway service uses separate Phase 2 Postgres database
- [ ] Phase 2 public URL loads successfully
- [ ] `/health` returns ok

## Natural-Language Intake Validation

- [ ] Missing Info Scenario asks for customer ID and order ID
- [ ] Invalid Identifier Scenario blocks workflow start
- [ ] Complete Cracked Screen Scenario extracts customer and order IDs
- [ ] Unknown valid-format customer scenario extracts IDs and routes
- [ ] Eligible Manufacturing Defect Scenario extracts IDs and routes
- [ ] Router does not decide eligibility, guardrails, replacement creation, approval, or escalation

## Multi-Turn Clarification Validation

- [ ] Initial incomplete request creates clarification question
- [ ] User reply with customer/order IDs updates same intake session
- [ ] Original customer request is preserved
- [ ] Router becomes ready after required facts are collected
- [ ] Run Governed Workflow remains disabled until ready
- [ ] Conversation context supports clarification only
- [ ] Workflow state still controls execution

## Governed Workflow Outcome Validation

- [ ] Missing info does not start workflow
- [ ] Invalid ID does not start workflow
- [ ] Cracked screen returns `not_eligible` and guardrail block
- [ ] Cracked screen does not create replacement request
- [ ] Unknown valid-format customer escalates after identity verification failure
- [ ] Eligible manufacturing defect returns `eligible`
- [ ] Eligible manufacturing defect has inventory available
- [ ] Eligible manufacturing defect receives guardrail allow
- [ ] Eligible manufacturing defect creates replacement request
- [ ] Customer response does not claim shipment occurred

## LLM Drafting Validation

- [ ] OpenAI drafting runs only after workflow decision
- [ ] LLM does not decide eligibility
- [ ] LLM does not create replacement request
- [ ] LLM draft passes validation before use
- [ ] Unsafe draft falls back to deterministic response
- [ ] Token usage appears only when provider returns usage metadata

## Audit and Trace Validation

- [ ] `workflow_runs` are persisted
- [ ] `audit_events` are persisted
- [ ] `human_reviews` are persisted when applicable
- [ ] Intake session includes a `correlation_id`
- [ ] Clarification replies preserve the same `correlation_id`
- [ ] Governed workflow receives the intake `correlation_id`
- [ ] Workflow final state includes the same `correlation_id`
- [ ] Audit events include the same `correlation_id`
- [ ] `GET /api/correlation/{correlation_id}` returns intake/workflow/audit linkage when available
- [ ] Trace Context panel shows correlation ID, intake session ID, workflow ID, LangSmith project, and tracing status
- [ ] LangSmith tracing status endpoint returns enabled when configured
- [ ] LangSmith project receives intake session trace
- [ ] LangSmith project receives workflow trace
- [ ] No fake trace links are displayed
- [ ] Audit replay and LangSmith tracing are treated as complementary

## Evaluation Pipeline Validation

- [ ] Golden scenarios are business-readable
- [ ] Golden scenarios are machine-checkable
- [ ] Evaluation runner covers missing info, invalid ID, block, escalate, and allow/action outcomes
- [ ] Deterministic assertions validate control-model behavior
- [ ] Evaluation does not require OpenAI key
- [ ] Evaluation does not require LangSmith key
- [ ] `pytest backend/tests/test_evaluation_pipeline.py` passes

## Control Monitoring Dashboard Validation

- [ ] Monitoring Dashboard tab loads
- [ ] `GET /api/monitoring/summary` returns real persisted workflow counts
- [ ] `GET /api/monitoring/runs` returns recent runs with workflow type, correlation ID, outcome, audit event count, and tool-call count
- [ ] `GET /api/monitoring/outcomes` returns supported workflow types and persisted workflow-run outcomes
- [ ] Outcome filter excludes intake-only values such as clarification-required and invalid-input
- [ ] Workflow type must be selected before KPI values are displayed
- [ ] Cracked-screen scenario increments blocked outcome count
- [ ] Unknown valid-format customer scenario increments escalated outcome count
- [ ] Eligible manufacturing defect scenario increments allowed/action and replacement request counts
- [ ] LLM token totals appear only when provider usage metadata exists in persisted final state
- [ ] Dashboard does not display fake cost, latency, trace links, or synthetic monitoring values
- [ ] Audit drilldown loads persisted audit events for a selected workflow run
- [ ] Dashboard clearly distinguishes DecisionTrace business/control monitoring from LangSmith execution tracing

## Merge Readiness

- [ ] README links to this Phase 2 validation checklist
- [ ] Roadmap links to this Phase 2 validation checklist
- [ ] No duplicate phase-specific architecture, executive summary, or roadmap files were created
- [ ] Backend code is unchanged for this documentation cleanup
- [ ] Frontend code is unchanged for this documentation cleanup
- [ ] Tests are unchanged for this documentation cleanup
- [ ] Deployment configuration is unchanged
- [ ] Screenshots are unchanged
- [ ] GitHub release tags are unchanged
- [ ] API routes are unchanged
- [ ] Database schema is unchanged
- [ ] `backend/.venv/bin/pytest` passes
- [ ] `node --check frontend/app.js` passes
- [ ] `git diff --check` passes

## Local Validation Commands

```bash
git checkout phase-2/intake-router
git pull origin phase-2/intake-router

backend/.venv/bin/pytest
backend/.venv/bin/pytest backend/tests/test_evaluation_pipeline.py
node --check frontend/app.js
git diff --check
```
