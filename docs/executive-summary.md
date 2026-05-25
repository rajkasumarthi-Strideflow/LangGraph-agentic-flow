# WarrantyWise Executive Summary

## Overview

WarrantyWise is an enterprise AI architecture capstone demonstrating a governed, auditable, production-aware agentic warranty replacement workflow. It shows how customer support automation can be designed around state, policies, tools, guardrails, persistence, and human review rather than relying on an unconstrained chatbot.

The Phase 1 implementation is deployed publicly on Railway and includes a FastAPI backend, browser UI, LangGraph workflow, governed mock tools, SQLAlchemy persistence, and Postgres-compatible audit storage.

The project is intentionally scoped to demonstrate enterprise architecture patterns: controlled decisioning, explainable workflow execution, safe action boundaries, and a persistent audit trail.

## Business Problem

Warranty replacement decisions require identity verification, order lookup, policy review, eligibility determination, inventory check, controlled action execution, customer-safe communication, and auditability. Without these controls, a support automation system can approve unsupported replacements, cite stale policy, expose unnecessary data, or fail to explain why a customer outcome occurred.

## Solution Summary

WarrantyWise uses:

- FastAPI for the backend API
- LangGraph for stateful workflow orchestration
- Governed mock tools for identity, order, policy, eligibility, inventory, replacement, escalation, and response generation
- Deterministic guardrails to block unsafe replacement creation
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

WarrantyWise reduces manual triage for common warranty requests while preventing unsupported replacement actions. It improves consistency of policy application, creates an auditable decision trail, supports future cost tracking and optimization, and provides a reusable architecture pattern for other customer support workflows.

The [Cost Model v1](cost-model.md) outlines how the architecture will estimate and control LLM, tool, retrieval, audit, observability, infrastructure, and human review costs.

The [Agentforce mapping](agentforce-mapping.md) translates the same architecture into Salesforce-native concepts such as Agent Script, subagents, actions, variables, available-when filters, and Agentforce DX.

## Phase 1 Scope

Phase 1 implements synthetic domain data, a deterministic warranty workflow, the cracked-screen scenario, no automatic replacement for excluded accidental damage, persisted workflow/audit/human review records, and a deployed demo.

The primary scenario is intentionally nuanced: the customer is inside the 12-month warranty window, but the cracked screen is excluded because the current policy excludes accidental damage. The correct outcome is a blocked replacement request with a safe customer explanation and persisted audit trail.

## Current Limitations

- Mock data only
- No real Salesforce integration
- No real customer authentication
- No real fulfillment/shipping integration
- No real LLM call yet
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
