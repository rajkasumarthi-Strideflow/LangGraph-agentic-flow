# DecisionTrace AI Local Evaluations

This folder contains the Step 28A local golden-scenario evaluation pipeline.

The pipeline validates the control model with deterministic assertions. It does
not call LangSmith evaluation APIs, Ragas, or an LLM judge. LLM-as-judge can be
added later for communication quality, tone, and faithfulness checks, but it
should not replace deterministic policy and guardrail assertions.

## Scenario Format

Golden scenarios are intentionally hybrid:

- Business-readable for Product, Operations, Audit, Risk, Security, Compliance, and Model Risk Management review.
- Machine-checkable for pytest automation and future LangSmith evaluations.

Each scenario describes the business situation first, then encodes the technical
assertions needed to validate the control model:

- `business_scenario` explains what the user is trying to do.
- `business_expectation` explains the expected business outcome.
- `control_model_expectation` explains which control should be validated.
- `expected` contains deterministic assertions used by the local runner.

Golden scenarios should describe the business expectation first, then encode the
technical assertions needed to validate the control model.

## What It Evaluates

The current golden scenarios cover:

- Missing customer/order identifiers require clarification.
- Invalid identifier formats block workflow start.
- Cracked-screen accidental damage is blocked by policy and guardrail.
- A syntactically valid unknown customer routes to workflow and escalates.
- A covered manufacturing defect allows governed replacement creation.

## Running Locally

From the repository root:

```bash
cd backend
python -m evals.runner
```

Or run through the normal test suite:

```bash
pytest
```

The runner uses the real intake router and governed LangGraph workflow. It does
not require OpenAI or LangSmith credentials.
