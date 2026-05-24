# Audit Schema

## Purpose

Audit logging makes each workflow run reconstructable. Instead of only seeing the final customer response, reviewers can inspect the event timeline and understand which node ran, which deterministic tool was called, what minimal inputs were used, what result was produced, which policy was referenced, and whether a guardrail allowed, blocked, or escalated the action.

Phase 1 uses an in-memory audit store. It is intentionally simple and local so tests can verify the workflow timeline without adding database persistence yet.

## AuditEvent Schema

| Field | Description |
| --- | --- |
| `event_id` | Unique audit event identifier. |
| `workflow_id` | Identifier for the workflow run. |
| `correlation_id` | Cross-system correlation identifier for tracing. |
| `event_type` | Controlled event type describing what happened. |
| `timestamp` | UTC timestamp when the event was recorded. |
| `actor` | Actor responsible for the event, currently `system`. |
| `node_name` | LangGraph node name when applicable. |
| `tool_name` | Tool function name when a node called a tool. |
| `input_summary` | Safe minimal input facts, such as `customer_id`, `order_id`, or `policy_id`. |
| `output_summary` | Safe minimal output facts, such as status, eligibility, or response type. |
| `policy_reference` | Current policy reference used in the decision, when applicable. |
| `guardrail_decision` | `allow`, `block`, or `escalate`, when applicable. |
| `reason` | Short explanation for the decision or event. |

Audit payloads must stay minimal. They should not include full customer profiles, payment data, or sensitive internal data.

## Event Types

- `workflow_started`
- `identity_verified`
- `order_lookup_completed`
- `policy_retrieved`
- `eligibility_checked`
- `inventory_checked`
- `guardrail_decision`
- `replacement_request_created`
- `human_escalation_created`
- `customer_response_generated`
- `workflow_completed`
- `workflow_failed`

## Cracked-Screen Timeline

For the primary customer request, “My laptop screen cracked after 9 months. Can I get a replacement?”, the expected audit timeline is:

1. `workflow_started`
2. `identity_verified`
3. `order_lookup_completed`
4. `policy_retrieved`
5. `eligibility_checked`
6. `guardrail_decision` with `guardrail_decision=block`
7. `customer_response_generated`
8. `workflow_completed`

There should be no `replacement_request_created` event because the current policy excludes accidental damage and cracked screens caused by drops, impact, or accidental damage.

## Eligible Replacement Timeline

For a future eligible issue, such as a covered manufacturing defect with available inventory, the expected audit timeline is:

1. `workflow_started`
2. `identity_verified`
3. `order_lookup_completed`
4. `policy_retrieved`
5. `eligibility_checked`
6. `inventory_checked`
7. `guardrail_decision` with `guardrail_decision=allow`
8. `replacement_request_created`
9. `customer_response_generated`
10. `workflow_completed`

## Enterprise Importance

Enterprise agentic workflows need auditability because actions must be explainable, reviewable, and controllable. The audit trail shows which source governed the decision, whether guardrails fired, why a case was escalated, and whether a write/action tool was allowed to run.

This is especially important for warranty decisions because customer-facing outcomes depend on identity, order ownership, policy status, eligibility, and inventory availability.

## Future Postgres Persistence

In a later step, the in-memory `AUDIT_EVENTS` list will move to Postgres. The event model, event types, and safe summary payloads should remain stable while storage changes from process memory to durable database tables with query support.
