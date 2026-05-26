# DecisionTrace AI Executive Summary

## Overview

DecisionTrace AI is an enterprise AI architecture capstone demonstrating governed, auditable, production-aware agentic workflows for customer-impacting decisions. It shows how AI-assisted automation can be designed around state, policies, tools, guardrails, persistence, controlled LLM response drafting, and human review rather than relying on an unconstrained chatbot.

The first implemented reference workflow is warranty replacement, branded historically in the repository as the WarrantyWise workflow. The same architecture pattern can extend to regulated financial and operational workflows such as credit approval, claims review, refund governance, subscription cancellation, and compliance exception handling.

The Phase 1 implementation is deployed publicly on Railway and includes a FastAPI backend, browser UI, LangGraph workflow, governed mock tools, controlled OpenAI response drafting, SQLAlchemy persistence, and Postgres-compatible audit storage.

The project is intentionally scoped to demonstrate enterprise architecture patterns: controlled decisioning, explainable workflow execution, safe action boundaries, and a persistent audit trail.

## Business Problem

Governed customer decisions require identity verification, context lookup, policy review, eligibility determination, action controls, customer-safe communication, and auditability. In the warranty replacement reference workflow, this means order lookup, warranty policy grounding, inventory checks, and replacement guardrails. Without these controls, an automation system can approve unsupported actions, cite stale policy, expose unnecessary data, or fail to explain why a customer outcome occurred.

## Solution Summary

DecisionTrace AI uses:

- FastAPI for the backend API
- LangGraph for stateful workflow orchestration
- Governed mock tools for identity, order, policy, eligibility, inventory, replacement, escalation, and response generation
- Deterministic guardrails to block unsafe replacement creation
- Controlled LLM response drafting for final customer-facing wording
- SQLAlchemy persistence for workflow runs, audit events, and human reviews
- Railway for public deployment
- A browser UI for workflow visibility

## Architecture at a Glance

```text
Browser UI
→ FastAPI
→ LangGraph workflow
→ governed tools
→ deterministic guardrails
→ controlled OpenAI response drafting
→ SQLAlchemy persistence
→ Postgres audit trail
```

## Enterprise Controls Demonstrated

- State-based workflow control
- Tool/action separation
- Policy-grounded eligibility
- Deterministic guardrails
- Human handoff simulation
- Audit event persistence
- Data minimization
- Safe customer response boundaries
- Separation of language generation from business decisioning
- Deployment with persistent database

## Business Value

DecisionTrace AI reduces manual triage for governed customer decisions while preventing unsupported actions. In the warranty replacement reference workflow, it improves consistency of policy application, creates an auditable decision trail, supports future cost tracking and optimization, and provides a reusable architecture pattern for other support, financial, insurance, and compliance workflows.

The [Cost Model v1](cost-model.md) outlines how the architecture will estimate and control LLM, tool, retrieval, audit, observability, infrastructure, and human review costs.

The [Agentforce mapping](agentforce-mapping.md) translates the same architecture into Salesforce-native concepts such as Agent Script, subagents, actions, variables, available-when filters, and Agentforce DX.

The [roadmap](roadmap.md) clarifies Phase 1 limitations and the planned path toward polished UX, controlled LLM use, observability, evaluation, cost telemetry, true HITL, CrewAI, MCP, A2A, and Agentforce implementation.

## Phase 1 Scope

Phase 1 implements synthetic domain data, a deterministic warranty replacement reference workflow, the cracked-screen scenario, no automatic replacement for excluded accidental damage, controlled LLM response drafting when configured, persisted workflow/audit/human review records, and a deployed demo.

The primary scenario is intentionally nuanced: the customer is inside the 12-month warranty window, but the cracked screen is excluded because the current policy excludes accidental damage. The correct outcome is a blocked replacement request with a safe customer explanation and persisted audit trail.

## Current Limitations

- Mock data only
- No real Salesforce integration
- No real customer authentication
- No real fulfillment/shipping integration
- No LLM intake classifier or multi-turn conversation yet
- No true LangGraph interrupt/resume yet
- No Ragas/Langfuse/LangSmith yet
- No CrewAI/MCP/A2A implementation yet

## Future Roadmap

- Polished workflow UI
- Controlled LLM response drafting
- True HITL with LangGraph interrupts
- Ragas evaluation
- Langfuse/LangSmith observability
- Cost model v1
- Agentforce mapping
- CrewAI review crew
- MCP tool/resource abstraction
- A2A fulfillment delegation

## Why This Matters

This project demonstrates that enterprise agentic AI is not just about giving an LLM tools. It is about designing the control plane around the model: state, tools, policies, guardrails, auditability, observability, human review, and cost governance.
