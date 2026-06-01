# DecisionTrace AI Safe Iteration Loop

## Purpose

This document explains how DecisionTrace AI should evolve from audit replay into observability-driven continuous improvement.

## Core Principle

Production failures should become regression tests.

## Loop Overview

```text
Workflow execution
→ audit/trace capture
→ issue detection
→ root-cause analysis
→ evaluator or regression case
→ prompt/tool/workflow fix
→ offline validation
→ controlled redeployment
→ production monitoring
```

## Current Phase 1 Foundation

DecisionTrace AI already captures workflow state, audit events, human review records, and LLM drafting metadata. This provides the foundation for audit replay.

Future tracing tools can enrich this with model spans, latency, token usage, retrieval spans, and tool traces. LangSmith tracing is optional on the Phase 2 tracing branch and should be enabled only with real environment configuration. Phase 1 does not include tracing.

## Phase 2 LangSmith Integration

LangSmith tracing can help identify recurring issues such as unsafe drafts, missing escalation conditions, routing failures, slow tool calls, or recurring policy-grounding errors.

Trace links can be shown in the UI once real run URLs are available from the backend. Do not fake trace links. Trace data should complement business audit events rather than replace them.

## From Audit Replay to Evaluation

Audit replay explains what happened. Tracing explains how execution happened. Evaluation determines whether behavior was correct. Regression tests prevent repeated failures.

DecisionTrace AI should use audit and trace evidence to create evaluator cases for recurring or high-impact issues. Those evaluator cases then become gates for prompt, tool, router, and workflow changes.

The `phase-2/evaluation-pipeline` branch adds the first local version of this loop with golden scenarios in `backend/evals/`. These scenarios use deterministic assertions to verify clarify, invalid input, block, escalate, and allow/action outcomes. Future LangSmith evaluation can reuse this scenario set as datasets and experiments, while preserving deterministic checks as the non-negotiable control layer.

Phase 2 also adds a shared `correlation_id` that connects intake sessions, governed workflow runs, audit events, and LangSmith trace metadata. This prepares DecisionTrace AI for production monitoring and replay views where business audit evidence and execution traces can be joined without relying on fake trace links or inferred identifiers.

## Phase 2 Control Monitoring

The Phase 2 control-monitoring dashboard turns persisted workflow data into business/control visibility. It summarizes real workflow runs, outcome categories, guardrail blocks, escalations, allowed actions, replacement requests, LLM drafting status, validation failures, token totals, audit event counts, and tool-call counts.

This layer is deliberately separate from LangSmith:

- LangSmith helps engineers debug execution traces.
- DecisionTrace monitoring helps Product, Operations, Audit, Risk, Security, Compliance, and MRM review governed decision outcomes.

The dashboard is reusable across future workflow types. The current workflow type is `warranty_replacement`, but future domains can emit the same core monitoring fields and inherit the same summary, filtering, and audit-drilldown pattern.

## Safe Deployment Gates

- Tests pass
- Prompt validation passes
- Evaluator coverage updated
- High-risk changes reviewed
- Rollback plan exists
- Production traces monitored after deployment
