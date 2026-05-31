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

## Safe Deployment Gates

- Tests pass
- Prompt validation passes
- Evaluator coverage updated
- High-risk changes reviewed
- Rollback plan exists
- Production traces monitored after deployment
