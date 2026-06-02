# DecisionTrace AI Phase 2 Release Notes

## Release Summary

Phase 2 extends DecisionTrace AI from a governed warranty workflow into a richer reference platform for validating the control model of AI-assisted workflows before production integration.

The core release message remains:

> Validate the control model before connecting production systems.

Warranty replacement remains Reference Workflow 1. Phase 2 adds natural-language intake, clarification, identifier validation, correlation, tracing, monitoring, and evaluation around that reference workflow so teams can see how governed AI-assisted decisions behave before exposing sensitive production systems.

## Key Capabilities Added in Phase 2

- Natural-language intake router
- Multi-turn clarification workflow
- Identifier format validation
- Natural-language-first UI
- Full outcome coverage:
  - Clarification required
  - Invalid identifier blocked
  - Cracked-screen guardrail block
  - Unknown valid-format customer escalation
  - Eligible manufacturing defect allow/action
- Eligible replacement happy path
- Shared correlation ID
- LangSmith tracing
- DecisionTrace control monitoring dashboard
- Local golden-scenario evaluation pipeline
- Business-readable and machine-checkable golden scenarios
- Optional LangSmith evaluation integration
- API reference
- Phase 2 validation checklist

## Validated Demo Scenarios

1. **Missing Info Scenario**
   - Expected outcome: router asks for customer and order identifiers, and the governed workflow does not start.

2. **Invalid Identifier Scenario**
   - Expected outcome: router blocks workflow start because `UNKNOWN_CUSTOMER` does not match the governed identifier format.

3. **Complete Cracked Screen Scenario**
   - Expected outcome: workflow starts, current policy is retrieved, eligibility is `not_eligible`, guardrail decision is `block`, and no replacement request is created.

4. **Unknown Valid-Format Customer Scenario**
   - Expected outcome: router allows workflow start because `cust_unknown_001` has a valid format, then workflow identity verification fails and escalation is created.

5. **Eligible Manufacturing Defect Scenario**
   - Expected outcome: workflow verifies identity/order, policy deems the power failure eligible, inventory is available, guardrail decision is `allow`, and a replacement request is created.

## Control Model Validation

Phase 2 validates the full control model:

- Router interprets the customer message and validates required facts.
- Router does not decide eligibility or execute business actions.
- Workflow verifies business truth through governed tools.
- Guardrails control whether action execution is allowed, blocked, or escalated.
- LLM drafts only after workflow decisions have been made.
- Audit replay reconstructs the business decision path.
- LangSmith traces execution behavior.
- DecisionTrace Monitoring aggregates business/control outcomes.
- Evaluations test the control model with deterministic assertions.

## Tool Adapter Accelerator Value

The accelerator value is that teams can swap the tool implementation layer without redesigning the control model.

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

## Observability and Monitoring

LangSmith monitors agent and workflow execution:

- Traces
- Spans
- Tool calls
- LLM calls
- Debugging context

DecisionTrace Monitoring tracks governed business workflow outcomes:

- Blocked outcomes
- Escalations
- Allowed/action outcomes
- Replacement requests
- Audit event counts
- Tool-call counts
- LLM drafting and validation status

Both are connected through the shared `correlation_id`.

## Evaluation

Local deterministic golden-scenario evaluation is the control-model source of truth.

Optional LangSmith evaluation integration can sync golden scenarios into a LangSmith dataset and run experiments for tracking and comparing evaluation runs over time.

LLM-as-judge is future work for response quality, tone, and faithfulness. It is not part of this release and should not replace deterministic control assertions.

## Known Boundaries

- Synthetic data only
- Controlled tool simulations only
- No real MuleSoft or client APIs connected yet
- No real Salesforce or Agentforce integration yet
- No production authentication or security model yet
- Intake sessions use a lightweight Phase 2 implementation and are not yet persisted as long-term historical funnel metrics
- No fake telemetry, fake trace links, fake cost, or fake latency

## Future Roadmap

- Phase 3 second workflow using MCP-style tools/resources
- Recommended workflow: Credit Application Readiness Review, not automated credit approval
- Cost telemetry
- Cost-optimized orchestration
- Persistent intake funnel metrics
- Safety detector nodes
- τ-Bench-inspired dynamic agent evaluation
- LLM-as-judge response quality evaluation
- Agentforce implementation prototype
- CrewAI review crew
