# DecisionTrace AI Executive Summary

This executive summary reflects the Phase 2 development branch of DecisionTrace AI. The Phase 1 stable release remains available on the `main` branch and GitHub release `v1.0-phase-1`.

Phase 1 established the governed workflow foundation. Phase 2 adds natural-language intake, multi-turn clarification, optional LangSmith tracing, local golden-scenario evaluation, shared correlation IDs, and a reusable control-monitoring dashboard. Future phases expand evaluation, safety controls, cost telemetry, and cost-aware orchestration.

## Overview

DecisionTrace AI is a working reference platform and prototype accelerator for governed, auditable AI-assisted workflows. It is designed to help teams validate the control model before connecting sensitive production systems.

The platform lets stakeholders evaluate the workflow, decision points, guardrails, audit evidence, human review paths, LLM response boundaries, and cost drivers using synthetic data and controlled tool simulations. This enables early alignment across Product, Operations, Audit, Risk, Security, Compliance, Legal, and Model Risk Management teams before production integration begins.

The accelerator value is not only faster prototyping; it is architectural continuity. Teams can validate the control model using synthetic data and controlled tool simulations, then connect the same governed workflow to enterprise API adapters when ready. This allows Product, Operations, Audit, Risk, Security, Compliance, Legal, and MRM stakeholders to align on the control model before production systems are exposed.

The first implemented reference workflow is warranty replacement, branded historically in the repository as the WarrantyWise workflow. DecisionTrace AI is broader than warranty replacement: the same architecture pattern can extend to regulated financial and operational workflows such as credit approval, claims review, refund governance, subscription cancellation, and compliance exception handling.

The Phase 1 implementation is deployed publicly on Railway and includes a FastAPI backend, browser UI, LangGraph workflow, controlled tool simulations, controlled OpenAI response drafting, SQLAlchemy persistence, and Postgres-compatible audit storage. Phase 1 is not presented as production-ready or regulatory-compliant; it demonstrates patterns required for governed workflows before production integration.

The project is intentionally scoped to demonstrate enterprise architecture patterns: controlled decisioning, explainable workflow execution, safe action boundaries, and a persistent audit trail.

## Business Problem

Governed customer decisions require identity verification, context lookup, policy review, eligibility determination, action controls, customer-safe communication, and auditability. In the warranty replacement reference workflow, this means order lookup, warranty policy grounding, inventory checks, and replacement guardrails. Without these controls, an automation system can approve unsupported actions, cite stale policy, expose unnecessary data, or fail to explain why a customer outcome occurred.

## Solution Summary

DecisionTrace AI uses:

- FastAPI for the backend API
- LangGraph for stateful workflow orchestration
- Controlled tool simulations for identity, order, policy, eligibility, inventory, replacement, escalation, and response generation
- Deterministic guardrails to block unsafe replacement creation
- Controlled LLM response drafting for final customer-facing wording
- SQLAlchemy persistence for workflow runs, audit events, and human reviews
- Railway for public deployment
- A browser UI for workflow visibility

Once the control model is validated, tool implementations can be connected to enterprise API adapters without redesigning the workflow architecture. The LangGraph workflow, state model, guardrails, audit logging, LLM response drafting boundary, and UI telemetry can remain stable while the tool layer is connected to systems such as CRM, order management, policy/knowledge repositories, inventory, approval engines, or case management platforms.

Executive implementation pattern:

```text
Governed workflow
→ controlled tool contract
→ enterprise API adapter
→ system of record
```

Examples include `check_inventory` connecting to a MuleSoft inventory API, `lookup_order` connecting to an order management API, `retrieve_policy` connecting to a policy or knowledge API, and `create_case` or `create_replacement_request` connecting to a CRM or workflow API.

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

DecisionTrace AI provides a fast, cost-effective way to validate the control model for AI-assisted workflows before production integration. In the warranty replacement reference workflow, it shows how teams can improve consistency of policy application, prevent unsupported actions, create an auditable decision trail, support future cost tracking and optimization, and reuse the same architecture pattern for support, financial, insurance, and compliance workflows.

The [Cost Model v1](cost-model.md) outlines how the architecture will estimate and control LLM, tool, retrieval, audit, observability, infrastructure, and human review costs.

The [Agentforce mapping](agentforce-mapping.md) translates the same architecture into Salesforce-native concepts such as Agent Script, subagents, actions, variables, available-when filters, and Agentforce DX.

The [roadmap](roadmap.md) clarifies Phase 1 limitations and the planned path toward polished UX, controlled LLM use, observability, evaluation, cost telemetry, true HITL, CrewAI, MCP, A2A, and Agentforce implementation.

Future phases will extend DecisionTrace AI from audit replay into safe iteration: workflow traces and production issues can be converted into evaluation cases and regression tests, enabling teams to improve agent behavior without weakening governance controls.

The Phase 2 monitoring layer complements LangSmith by separating business/control monitoring from execution tracing. LangSmith can show how a run executed; DecisionTrace shows what governed outcome occurred, whether guardrails blocked or allowed action, how many audit/tool events were recorded, and how the run connects through a shared correlation ID.

## Phase 1 Scope

Phase 1 implements synthetic domain data, controlled tool simulations, a deterministic warranty replacement reference workflow, the cracked-screen scenario, no automatic replacement for excluded accidental damage, controlled LLM response drafting when configured, persisted workflow/audit/human review records, and a deployed demo.

The primary scenario is intentionally nuanced: the customer is inside the 12-month warranty window, but the cracked screen is excluded because the current policy excludes accidental damage. The correct outcome is a blocked replacement request with a safe customer explanation and persisted audit trail.

Active telemetry is real even though the business data is synthetic. Workflow state, audit events, tool-call counts, human review records, OpenAI model metadata, and token usage are generated from actual workflow execution, database writes, backend API responses, and provider usage metadata when OpenAI is configured.

## Current Limitations

- Synthetic data only
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
