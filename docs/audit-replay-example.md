# DecisionTrace AI Audit Replay Example

## Purpose

This document shows how DecisionTrace AI supports audit replay for an enterprise agentic AI workflow. The goal is to reconstruct what happened, which policy was used, what decision was made, why the replacement was blocked, and what response was sent.

The cracked-screen warranty replay is the first reference audit scenario. It uses persisted workflow state plus audit events to explain the decision path for the warranty replacement reference workflow.

## Replay Scenario

- Customer request: “My laptop screen cracked after 9 months. Can I get a replacement?”
- Customer ID: `cust_primary_001`
- Order ID: `ord_laptop_001`
- Product family: `laptop`
- Purchase age: `9 months`
- Business question: is the customer eligible for warranty replacement?

## Expected Decision

The product is within the 12-month warranty window. However, the current warranty policy excludes accidental damage, including cracked screens caused by drops, impact, or accidental damage.

Therefore, the workflow should block automatic replacement creation. The system may route ambiguous defect claims to human review in future phases, but the Phase 1 cracked-screen request is not automatically eligible.

Expected outcome:

- `eligibility_status = not_eligible`
- `guardrail_decision = block`
- `replacement_request_id = null`
- Customer response does not claim a replacement was created.

## Audit Replay Timeline

| Step | Event Type | Node | Tool | What Happened | Evidence / Output | Audit Significance |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `workflow_started` | N/A | N/A | Workflow run started for the customer request. | `customer_id=cust_primary_001`, `order_id=ord_laptop_001` | Establishes the workflow run and correlation context. |
| 2 | `identity_verified` | `verify_identity` | `verify_identity` | Customer identity verification ran. | `identity_verified=true` | Confirms the workflow did not proceed without identity verification. |
| 3 | `order_lookup_completed` | `lookup_order` | `lookup_order` | Order was retrieved and authorized for the customer. | `order_status=delivered`, `product_family=laptop`, `purchase_age_months=9` | Proves order ownership and delivered status were checked. |
| 4 | `policy_retrieved` | `retrieve_warranty_policy` | `retrieve_warranty_policy` | Current laptop warranty policy was retrieved. | `policy_reference=pol_laptop_us_current_v2#v2.0` | Shows the decision used the current policy reference. |
| 5 | `eligibility_checked` | `check_replacement_eligibility` | `check_replacement_eligibility` | Eligibility was evaluated under the current policy. | `eligibility_status=not_eligible`; cracked screens caused by drops, impact, or accidental damage are excluded. | Explains why the request is not automatically eligible. |
| 6 | `guardrail_decision` | `guardrail_check` | N/A | Replacement creation guardrail evaluated the state. | `guardrail_decision=block` | Proves the write/action path was blocked because eligibility was `not_eligible`. |
| 7 | `customer_response_generated` | `generate_customer_response` | `generate_customer_response` | Customer-safe response was generated. | Response explains the item is not automatically eligible under the current warranty policy. | Confirms the customer response did not overpromise replacement creation. |
| 8 | `workflow_completed` | N/A | N/A | Workflow completed successfully. | `workflow_status=completed` | Confirms the workflow ended cleanly after the block decision. |

## State Snapshot to Review

Representative state snapshot:

```json
{
  "workflow_id": "wf_example_cracked_screen",
  "correlation_id": "corr_example_cracked_screen",
  "customer_request": "My laptop screen cracked after 9 months. Can I get a replacement?",
  "customer_id": "cust_primary_001",
  "order_id": "ord_laptop_001",
  "product_id": "prod_laptop_001",
  "product_family": "laptop",
  "identity_verified": true,
  "customer_authorized": true,
  "order_retrieved": true,
  "order_status": "delivered",
  "purchase_age_months": 9,
  "policy_reference": "pol_laptop_us_current_v2#v2.0",
  "policy_version": "2.0",
  "eligibility_status": "not_eligible",
  "eligibility_reason": "Accidental damage and cracked screens caused by drops, impact, or accidental damage are excluded by the current warranty policy.",
  "inventory_available": null,
  "guardrail_decision": "block",
  "replacement_request_id": null,
  "escalation_id": null,
  "customer_response": "Based on the current warranty policy, this item is not automatically eligible for replacement. Reason: Accidental damage and cracked screens caused by drops, impact, or accidental damage are excluded by the current warranty policy.",
  "workflow_status": "completed"
}
```

## API Replay Commands

Start a replay run:

```bash
curl -X POST <RAILWAY_PUBLIC_URL>/api/workflows/start \
  -H "Content-Type: application/json" \
  -d '{
    "customer_request": "My laptop screen cracked after 9 months. Can I get a replacement?",
    "customer_id": "cust_primary_001",
    "order_id": "ord_laptop_001"
  }'
```

Inspect persisted workflow state:

```bash
curl <RAILWAY_PUBLIC_URL>/api/workflows/<WORKFLOW_ID>
```

Inspect persisted audit timeline:

```bash
curl <RAILWAY_PUBLIC_URL>/api/workflows/<WORKFLOW_ID>/audit
```

## What the Auditor Can Prove

- The customer request was captured.
- Identity verification ran.
- Order lookup ran.
- Current policy was retrieved.
- Deprecated policy was not used.
- Eligibility was evaluated.
- Guardrail blocked replacement creation.
- No replacement request was created.
- Final customer response did not overpromise.
- The workflow completed successfully.

## What This Replay Does Not Yet Include

- No full LLM prompt/response observability trace yet.
- No token/cost trace yet.
- No Langfuse/LangSmith trace yet.
- No real LangGraph interrupt/resume yet.
- No real Salesforce/Agentforce execution log yet.

## Future Observability Extension

DecisionTrace AI audit replay explains what happened from a business/governance perspective. Langfuse or LangSmith tracing will explain how the LLM/agent execution happened from an observability perspective once deeper tracing is added.

Future trace fields may include:

- Model name/version
- Prompt
- Response
- Tokens
- Latency
- Tool spans
- Retrieval spans
- Cost estimate
- Guardrail spans

## Interview Talking Point

In this project, auditability is not an afterthought. Each workflow node emits structured audit events, and those events are persisted so a reviewer can reconstruct the decision path. This matters because enterprise agentic AI systems must be explainable, governable, and reviewable, especially when they influence customer-impacting actions.
