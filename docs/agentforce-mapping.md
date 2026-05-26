# DecisionTrace AI Agentforce Mapping

## Purpose

This document maps the custom DecisionTrace AI LangGraph architecture to current Salesforce Agentforce concepts. The mapping uses the warranty replacement workflow as the first reference implementation. The goal is to show how the same enterprise agentic architecture pattern could be implemented in a Salesforce-native way.

This is a conceptual mapping, not an implemented Salesforce or Agentforce integration. Current Agentforce terminology uses **subagents**. Older Salesforce references may still say “topics,” but this document uses “subagents” for the target architecture.

## Current DecisionTrace AI Architecture Summary

```text
Browser UI
→ FastAPI API layer
→ LangGraph workflow
→ governed mock tools
→ deterministic guardrails
→ SQLAlchemy persistence
→ Postgres audit trail
```

DecisionTrace AI currently implements the warranty replacement reference workflow outside Salesforce using FastAPI, LangGraph, deterministic Python tools, controlled OpenAI response drafting, SQLAlchemy, and Railway Postgres-compatible persistence.

## Agentforce Target Architecture

```text
Agentforce Agent
→ Agent Script
→ Subagents
→ Agentforce Actions
→ Salesforce data / Knowledge / Flow / Apex / external APIs
→ Guardrails / available-when filters / deterministic expressions
→ Case / approval / queue handoff
→ Salesforce audit/event logs or external observability
```

Agent Script combines natural language instructions with deterministic expressions for business rules, conditionals, transitions, variable setting, subagent selection, and action selection. Agent Script variables track state across subagents and conversation turns. Agentforce actions perform tasks such as calling Flow, Apex, prompt templates, or other action targets.

## Concept Mapping Table

| DecisionTrace AI / LangGraph Concept | Agentforce Concept | Mapping Explanation |
| --- | --- | --- |
| LangGraph workflow | Agent Script controlled flow / subagent transitions | Agent Script can define deterministic flow and transition logic between subagents. |
| LangGraph state | Agent Script variables | Control facts become variables shared across subagents and turns. |
| LangGraph nodes | Subagent logic blocks or action orchestration | Each node maps to subagent reasoning, deterministic logic, or action invocation. |
| Conditional edges | Agent Script if/else, transitions, available-when conditions | Branching logic maps to deterministic expressions and action/subagent availability. |
| Guardrail node | Agent Script rules, Flow/Apex policy checks, available-when filters | Replacement creation should be hidden and blocked unless deterministic conditions pass. |
| Mock tools | Agentforce actions | DecisionTrace AI tools map to Flow, Apex, prompt template, external service, or Knowledge-backed actions. |
| Policy retrieval | Knowledge/Data Cloud/action-backed grounding | Current policy retrieval maps to approved policy grounding with metadata filters. |
| `create_replacement_request` | Guarded write/action | Could be a Flow or Apex action with server-side eligibility enforcement. |
| `escalate_to_human` | Service Case, queue, approval, Omni-Channel handoff | Escalation creates or routes a review package to a human path. |
| Customer response generation | Prompt Template or response subagent | LLM can draft language, but should rely on deterministic state and approved policy facts. |
| `audit_events` table | Salesforce logs, custom audit object, Platform Events, external observability | Audit events can be stored natively or exported to a centralized log store. |
| `workflow_runs` table | Case/session/custom object state | Final workflow state can map to a Case, session record, or custom object. |
| `human_reviews` table | Case comments, approval records, tasks, review custom object | Human review decisions map to service review records or approvals. |
| FastAPI frontend/API | Salesforce channel, Experience Cloud, Agent API, or external app | External clients can interact with Agentforce through supported APIs/channels. |
| Railway deployment | Salesforce platform runtime plus optional external services | A Salesforce-native implementation would reduce custom app hosting for core agent logic. |
| Postgres persistence | Salesforce data store plus optional external lake/log store | Native implementation can use Salesforce objects/events, with external persistence for enterprise analytics. |

## Proposed Subagent Design

### Warranty Intake Subagent

- **Purpose:** Capture the customer request and identify the warranty replacement intent.
- **Responsibilities:** Extract customer request facts, confirm required identifiers, initialize variables, route to order context.
- **Allowed actions:** Intent classification, customer ID capture, order ID capture, request summarization.
- **Should not do:** Decide eligibility, create replacements, or cite policy without grounding.

### Order Context Subagent

- **Purpose:** Verify customer/order relationship and retrieve product context.
- **Responsibilities:** Check identity, authorize order ownership, retrieve order and product facts.
- **Allowed actions:** `verify_identity`, `lookup_order`, account/order Flow or Apex actions.
- **Should not do:** Create replacement requests or override authorization failures.

### Warranty Policy Subagent

- **Purpose:** Retrieve the current approved policy for the product family and region.
- **Responsibilities:** Ground the decision in current policy, filter stale/deprecated content, set policy variables.
- **Allowed actions:** Knowledge grounding, Data Cloud/Data 360 retrieval, policy Apex/Flow lookup.
- **Should not do:** Use deprecated policy sources or invent coverage rules.

### Replacement Eligibility Subagent

- **Purpose:** Determine eligibility and replacement action availability.
- **Responsibilities:** Evaluate policy, order status, inventory, and guardrail variables.
- **Allowed actions:** Eligibility Flow/Apex action, inventory action, guardrail checks.
- **Should not do:** Depend only on LLM reasoning for eligibility or write/action approval.

### Customer Response Subagent

- **Purpose:** Generate the final customer-facing explanation.
- **Responsibilities:** Use workflow variables and policy facts to produce safe response language.
- **Allowed actions:** Prompt template for response drafting, response formatting action.
- **Should not do:** Promise replacement creation unless a replacement ID exists.

### Human Handoff Subagent

- **Purpose:** Route uncertain, unauthorized, conflicting, or exception cases to human review.
- **Responsibilities:** Create evidence package, route to queue/case/approval, summarize next action.
- **Allowed actions:** Create Case, assign Queue, launch Approval Process, Omni-Channel handoff.
- **Should not do:** Resolve high-risk exceptions without human review.

## Agent Script Variables

WarrantyWorkflowState fields map naturally to Agent Script variables:

- `customer_id`
- `order_id`
- `product_id`
- `product_family`
- `identity_verified`
- `customer_authorized`
- `order_retrieved`
- `order_status`
- `purchase_age_months`
- `policy_reference`
- `policy_version`
- `eligibility_status`
- `eligibility_reason`
- `inventory_available`
- `guardrail_decision`
- `replacement_request_id`
- `escalation_required`
- `escalation_reason`

Variables should track control facts needed for routing, action input/output, customer communication, and auditability. They should not store every piece of raw data. Full customer profiles, payment data, and large raw policy payloads should stay outside the agent context unless specifically required and governed.

## Agentforce Actions

| DecisionTrace AI Tool | Agentforce Action Type | Possible Implementation | Risk Tier | Notes |
| --- | --- | --- | --- | --- |
| `verify_identity` | Flow or Apex Invocable Method | Check Contact/Account identity verification flags or call identity service | read | Return minimal identity status. |
| `lookup_order` | Flow, Apex, Named Query, external service | Query Order, Asset, Entitlement, or Commerce data | read | Return only required order/product facts. |
| `retrieve_warranty_policy` | Knowledge grounding, Data Cloud/Data 360, Flow/Apex | Retrieve approved current policy by product family, region, effective date | decision-support | Filter deprecated policy records. |
| `check_replacement_eligibility` | Flow or Apex Invocable Method | Apply warranty eligibility rules deterministically | decision-support | Should not rely only on LLM interpretation. |
| `check_inventory_availability` | Apex REST / external service callout | Query inventory/fulfillment service | read | Return availability and quantity summary. |
| `create_replacement_request` | Flow or Apex write action | Create replacement order/case/task after guardrails pass | write/action | Require server-side enforcement and confirmation where needed. |
| `escalate_to_human` | Flow, Case creation, Omni-Channel | Create Service Case, queue item, approval, or task | escalation | Include evidence package. |
| `generate_customer_response` | Prompt Template or response subagent | Draft customer-safe response from variables | generation | Must not invent replacement status. |

## Guardrails and Available-When Filters

The replacement creation action should only be available when:

- `identity_verified = true`
- `customer_authorized = true`
- `order_retrieved = true`
- `order_status = delivered`
- `policy_reference` is not empty
- `eligibility_status = eligible`
- `inventory_available = true`
- `escalation_required = false`

Available-when filters reduce the chance that the agent even sees or chooses an action when it should not be available. Deterministic Flow/Apex checks should enforce the same controls server-side. The UI/agent layer can hide the action, but the action target must still reject unsafe execution.

## Deterministic Control vs LLM Reasoning

Agentforce can use LLM reasoning for natural language understanding and response generation. Deterministic Agent Script expressions, Flow, Apex, and available-when filters should control high-risk business decisions and action availability.

Warranty eligibility and replacement creation should not depend only on model reasoning.

Principle: LLM reasoning can help interpret and communicate; deterministic controls should govern eligibility, authorization, and action execution.

## Policy Grounding

Warranty policy retrieval could map to:

- Salesforce Knowledge
- Data Cloud/Data 360 grounding
- Approved policy records
- Apex/Flow action that returns the current approved policy
- Metadata filters such as `product_family`, `region`, `effective_date`, `approval_status`, and `audience`

Deprecated policy sources should be filtered out or deprioritized, similar to the DecisionTrace AI source-priority design. The target policy retrieval action should return a policy reference/version so audit replay can prove which policy governed the decision.

## Human Handoff and Review

The current human review simulation could map to:

- Create Service Case
- Route to Queue
- Omni-Channel handoff
- Approval Process
- Flow Orchestration
- Human review task

A true Agentforce implementation should preserve the evidence package: customer request, order facts, policy reference, eligibility result, guardrail decision, and recommended next action.

## Audit and Replay Mapping

DecisionTrace AI audit events map to Agentforce/Salesforce audit needs:

- Customer request
- Selected subagent
- Action calls
- Action inputs/outputs summary
- Policy reference
- Eligibility status
- Guardrail decision
- Human handoff details
- Final customer response
- Model/action/policy versions where available

Some audit data could be stored in Salesforce custom objects, Platform Events, Event Monitoring, an external log store, or an observability platform. The key principle is to preserve enough structured evidence to reconstruct customer-impacting decisions.

## Agentforce DX and Version Control

Agentforce DX and Agent Script can help version-control the agent definition as metadata, similar to how this capstone version-controls LangGraph code, tool definitions, docs, tests, and deployment config.

Version-controlled assets can include:

- Agent Script files
- Metadata-driven changes
- Source control branches and pull requests
- Review/approval process
- Environment promotion
- Test/preview before production

## Agent API / External Channel Mapping

The current FastAPI/browser layer could map to an external channel using Agent API or a Salesforce-hosted channel.

Conceptual flow:

1. External app starts a session.
2. External app sends user message.
3. Agentforce agent processes through Agent Script/subagents/actions.
4. External app receives agent response.
5. External app streams responses if needed.
6. External app ends the session.

This is conceptual only; DecisionTrace AI does not currently implement Agent API integration.

## What Should Stay Outside Agentforce

- Enterprise data warehouse analytics
- External fulfillment agent orchestration if owned by another platform
- Cross-platform A2A delegation
- Heavy offline evaluation pipelines
- Long-term observability/cost dashboards if centralized outside Salesforce
- Non-Salesforce services where enterprise architecture requires external ownership

## Implementation Roadmap

- **Phase A:** Agentforce design mapping
- **Phase B:** Define subagents and variables
- **Phase C:** Implement read/decision-support actions
- **Phase D:** Implement grounding and source-priority controls
- **Phase E:** Add guarded write actions and available-when filters
- **Phase F:** Add human handoff
- **Phase G:** Add audit/replay and monitoring
- **Phase H:** Test with simulated and live action preview

## Interview Talking Points

### How does LangGraph state map to Agentforce?

LangGraph state maps to Agent Script variables. Variables should store durable control facts such as identity status, order status, policy reference, eligibility status, guardrail decision, and escalation reason.

### How do tools map to Agentforce actions?

DecisionTrace AI tools map to Agentforce actions backed by Flow, Apex, prompt templates, Knowledge/Data Cloud grounding, or external service callouts.

### Why use available-when filters?

Available-when filters prevent unsafe or irrelevant actions from being available to the agent. They reduce action risk before the model can choose a tool.

### Where should deterministic controls live?

They should live in Agent Script expressions, Flow, Apex, and action targets. High-risk business decisions should not rely only on LLM reasoning.

### How would you prevent the agent from creating an unsupported replacement?

Hide the replacement action unless required variables pass, and enforce the same conditions in Flow/Apex before any write occurs.

### How would auditability work in Agentforce?

Record subagent selection, action calls, summarized inputs/outputs, policy references, eligibility status, guardrail decisions, human handoff details, and final responses in Salesforce logs, custom objects, Platform Events, or an external observability store.

### How would this be version-controlled?

Use Agentforce DX and Agent Script metadata in source control, with pull requests, validation, preview/testing, and environment promotion before production.

## References

- [Agent Script](https://developer.salesforce.com/docs/ai/agentforce/guide/agent-script.html)
- [Agent Script Variables](https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-variables.html)
- [Agent Script Actions](https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-actions.html)
- [Agentforce DX](https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-nga-script.html)
- [Agentforce APIs and SDKs](https://developer.salesforce.com/docs/ai/agentforce/guide/get-started-agents.html)
