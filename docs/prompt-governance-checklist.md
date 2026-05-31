# DecisionTrace AI Prompt Governance Checklist

## Purpose

This checklist defines how prompts should be governed as DecisionTrace AI expands beyond controlled response drafting into natural-language intake, multi-turn clarification, and workflow-specific assistants.

## Why Prompt Governance Matters

Prompts are not just text. In agentic systems, prompts influence routing, tool use, response tone, escalation, and business interpretation.

Poor prompt design can create ambiguity, unsafe action selection, missed escalation, hallucinated policy interpretation, or unsupported customer promises. As LLM usage expands, prompts should be treated as governed workflow assets with ownership, versioning, tests, and approval criteria.

The Phase 2 intake router prompt boundary is intentionally narrow: classify intent, extract structured facts, identify missing or invalid fields, ask clarification questions, and route to a controlled workflow only after deterministic validation passes. It must not decide eligibility, claim approval, create replacement requests, override guardrails, or imply that a business action has been executed.

The current multi-turn clarification flow stores session context in memory for Phase 2 development. That context is used only to preserve the original request and collect required facts such as customer ID and order ID. Future phases can persist sessions and trace every turn, but workflow state remains the source of truth for execution.

## Prompt Scope

- [ ] What is the prompt responsible for?
- [ ] What is explicitly out of scope?
- [ ] What workflow or subagent uses it?
- [ ] What business decision should it not make?
- [ ] What tool/action should it not call or imply?

## Required Inputs

- [ ] What state fields are required?
- [ ] What policy references are required?
- [ ] What user message fields are required?
- [ ] What tool outputs are required?
- [ ] What should happen if required inputs are missing?

## Output Contract

- [ ] Is structured output required?
- [ ] What fields must be present?
- [ ] What fields are optional?
- [ ] What values are allowed?
- [ ] What should the model do when uncertain?
- [ ] What validation layer checks the output?

## Guardrails and Prohibited Claims

- [ ] Must not approve an action unless workflow state allows it.
- [ ] Must not claim replacement/refund/approval was created unless the corresponding ID exists.
- [ ] Must not override policy.
- [ ] Must not expose internal implementation details.
- [ ] Must not invent missing data.
- [ ] Must escalate or ask clarification when facts are missing.

## Escalation Conditions

- [ ] Low confidence
- [ ] Conflicting policy
- [ ] Missing required facts
- [ ] High-risk action
- [ ] Customer dispute
- [ ] Policy exception request
- [ ] Sensitive data concern
- [ ] Repeated failure/retry loop

## Prompt Injection and Abuse Considerations

- [ ] Does the prompt instruct the model to ignore user attempts to override policy?
- [ ] Does the prompt preserve tool/action boundaries?
- [ ] Does the prompt limit exposure of internal instructions?
- [ ] Does the prompt treat user-provided policy claims as untrusted unless verified?

## Testing Requirements

- [ ] Golden test cases
- [ ] Unsafe output tests
- [ ] Missing-data tests
- [ ] Conflicting-policy tests
- [ ] Escalation tests
- [ ] Regression tests from production failures
- [ ] Human review sampling

The `phase-2/evaluation-pipeline` branch starts this discipline with local golden scenarios in `backend/evals/`. Prompt-related changes should preserve these deterministic control assertions before any future LLM-as-judge checks are added for tone or response quality.

## Approval and Versioning

- [ ] Prompt owner identified
- [ ] Version tracked
- [ ] Change reason documented
- [ ] Tests updated
- [ ] Risk review completed when needed
- [ ] Deployment approved
