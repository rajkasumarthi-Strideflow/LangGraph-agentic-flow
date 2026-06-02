# DecisionTrace AI Demo Script

This script supports a 5–7 minute Phase 2 walkthrough of DecisionTrace AI.

## Opening Positioning

This is DecisionTrace AI: a governed workflow reference platform and prototype accelerator for AI-assisted customer decisions.

The core message is simple:

> Validate the control model before connecting production systems.

The first implemented reference workflow is warranty replacement. That does not mean DecisionTrace AI is only a warranty app. Warranty replacement is Reference Workflow 1 because it demonstrates the same controls needed in higher-stakes workflows: policy grounding, identity and order checks, guardrails, human review, audit replay, observability, monitoring, and evaluation.

## Architecture Overview

The Phase 2 architecture is:

```text
Natural Language Intake
→ Stateful Router
→ Multi-turn Clarification
→ Governed LangGraph Workflow
→ Governed Tools
→ Deterministic Guardrails
→ Controlled OpenAI Response Drafting
→ Persisted Audit Trail
→ LangSmith Tracing
→ DecisionTrace Monitoring
→ Golden-scenario Evaluation
```

The router interprets the customer message and collects required facts. It does not decide eligibility or execute business actions. The LangGraph workflow remains the control layer. It verifies identity, retrieves order and policy context, checks eligibility, enforces guardrails, creates or blocks actions, escalates when needed, and generates the final customer-safe response.

## Live Demo Walkthrough

Open the Phase 2 Railway app and start in the natural-language intake panel.

### 1. Missing Info Scenario

Click **Missing Info Scenario**:

> My laptop screen cracked after 9 months. Can I get a replacement?

Click **Start Intake / Analyze Request**.

Point out:

- The router identifies a warranty replacement request.
- It detects missing customer and order identifiers.
- It asks a clarification question.
- **Run Governed Workflow** stays disabled.

Message: the system does not start a governed workflow until required facts are collected.

### 2. Multi-turn Clarification

Reply with:

> Customer ID is cust_primary_001 and order ID is ord_laptop_001.

Point out:

- The same intake session is updated.
- The original request is preserved.
- The shared `correlation_id` remains stable.
- The router extracts and validates the identifiers.
- The workflow is now ready to start.

### 3. Invalid Identifier Scenario

Click **Invalid Identifier Scenario**.

Point out:

- The router treats user-provided identifiers as untrusted.
- `UNKNOWN_CUSTOMER` is blocked by deterministic identifier format validation.
- The workflow does not start.

Message: the router validates format only; the workflow verifies business truth later.

### 4. Complete Cracked Screen Scenario

Click **Complete Cracked Screen Scenario**, analyze it, then run the governed workflow.

Expected outcome:

- Identity is verified.
- Order is retrieved.
- Current warranty policy is retrieved.
- The screen issue is classified as accidental damage / cracked screen.
- `eligibility_status = not_eligible`.
- `guardrail_decision = block`.
- No `replacement_request_id` is created.
- The customer response does not claim replacement creation.

Point out audit replay as the business/governance trail.

### 5. Unknown Valid-Format Customer Scenario

Click **Unknown Customer Scenario**, analyze it, and run the workflow.

Expected outcome:

- Router allows start because `cust_unknown_001` has a valid format.
- Workflow identity verification fails.
- The case escalates.
- Human review simulation becomes available.

Message: format validation is not business validation. The governed workflow owns business truth.

### 6. Eligible Manufacturing Defect Scenario

Click **Eligible Manufacturing Defect Scenario**, analyze it, and run the workflow.

Expected outcome:

- Identity and order checks pass.
- Current policy is retrieved.
- Power failure / manufacturing defect is eligible.
- Inventory is available.
- `guardrail_decision = allow`.
- A governed replacement request is created.

Message: DecisionTrace can allow actions, but only after required controls pass.

## Correlation, Audit, and Observability

Show the Trace Context panel.

Point out:

- `intake_session_id`
- `correlation_id`
- `workflow_id`

The correlation ID connects intake, workflow, audit events, and LangSmith trace metadata.

Use this distinction:

- **Audit replay** is the business/governance trail: what happened, which policy was used, what decision was made, and why.
- **LangSmith tracing** is execution observability: how the router, workflow, tools, and LLM drafting executed.
- **DecisionTrace Monitoring** is business/control monitoring: blocked, escalated, allowed/action outcomes, audit events, tool calls, token metadata, and correlation-linked runs.

## Evaluation

DecisionTrace Phase 2 includes local golden-scenario evaluation.

Explain:

- Golden scenarios are business-readable and machine-checkable.
- Deterministic assertions validate the control model.
- Local pytest evaluations remain the source of truth.
- Optional LangSmith evaluation integration can sync the scenarios into datasets and run experiments for tracking and version comparison.
- LLM-as-judge is future work for response quality, tone, and faithfulness. It does not replace deterministic control assertions.

## Tool Adapter Accelerator Value

This is one of the most important enterprise architecture points:

> The accelerator value is that teams can swap the tool implementation layer without redesigning the control model.

Pattern:

```text
LangGraph node
→ governed tool interface
→ enterprise API adapter
→ MuleSoft / enterprise API endpoint
→ system of record
```

Example:

```text
check_inventory_availability node
→ check_inventory tool
→ InventoryAPIAdapter
→ MuleSoft GET /inventory/availability
→ SAP / Oracle / Salesforce / OMS inventory source
```

In a client implementation, simulated tools can be replaced with enterprise API wrappers while preserving the same LangGraph workflow, state model, guardrails, audit logging, correlation ID, monitoring dashboard, LangSmith tracing metadata, evaluation scenarios, and LLM response drafting boundary.

## Closing

DecisionTrace AI is not a warranty app. It is a governed workflow reference platform and prototype accelerator.

Warranty replacement is Reference Workflow 1. The larger value is the control model: natural-language intake, deterministic workflow execution, bounded tools, guardrails, audit replay, observability, monitoring, evaluation, and an adapter layer that can connect to enterprise APIs when the organization is ready.

## 30-Second Version

DecisionTrace AI validates the control model before connecting production systems. Phase 2 adds natural-language intake, multi-turn clarification, identifier validation, full outcome coverage, shared correlation IDs, LangSmith tracing, DecisionTrace monitoring, and deterministic golden-scenario evaluation. The first workflow is warranty replacement, but the platform pattern generalizes to governed customer decisions. Its accelerator value is architectural continuity: teams can replace simulated tools with enterprise API adapters without redesigning the workflow, guardrails, audit trail, monitoring, tracing, or evaluation model.
