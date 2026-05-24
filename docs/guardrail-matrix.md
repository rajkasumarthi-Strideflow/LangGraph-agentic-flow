# Guardrail Matrix

## Replacement Creation Guardrail

The replacement creation guardrail prevents the workflow from creating replacement requests unless identity, authorization, order, policy, eligibility, inventory, and escalation checks have all passed.

| Condition | Required Value | Failure Behavior | Audit Relevance |
| --- | --- | --- | --- |
| Customer identity | `identity_verified == true` | Route to human escalation. | Shows whether identity verification was satisfied before any action. |
| Customer authorization | `customer_authorized == true` | Route to human escalation. | Confirms the order belonged to the requesting customer. |
| Order retrieval | `order_retrieved == true` | Route to human escalation. | Records whether the workflow had valid order context. |
| Order status | `order_status == "delivered"` | Block or escalate; do not create replacement request. | Demonstrates delivered-order requirement was checked. |
| Policy reference | `policy_reference` exists | Route to human escalation. | Links the decision to the active policy source. |
| Eligibility | `eligibility_status == "eligible"` | If `not_eligible`, block replacement creation; if unknown or review required, escalate. | Records the policy outcome used to permit or deny the action. |
| Inventory | `inventory_available == true` | Route to human escalation; do not create replacement request. | Shows whether replacement stock was available at decision time. |
| Escalation state | `escalation_required == false` | Route to human escalation. | Prevents action while an unresolved review requirement exists. |
| Guardrail decision | `guardrail_decision == "allow"` | `block` generates a safe response; `escalate` routes to human review. | Captures the final governed decision before any write/action tool. |

For the primary cracked-screen scenario, eligibility is `not_eligible` because accidental damage and cracked screens caused by drops, impact, or accidental damage are excluded by the current warranty policy. The workflow must not create a replacement request for that scenario.
