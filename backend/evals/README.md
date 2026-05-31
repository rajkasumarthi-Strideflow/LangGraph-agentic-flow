# DecisionTrace AI Local Evaluations

This folder contains the Step 28A local golden-scenario evaluation pipeline.

The pipeline validates the control model with deterministic assertions. It does
not call LangSmith evaluation APIs, Ragas, or an LLM judge. LLM-as-judge can be
added later for communication quality, tone, and faithfulness checks, but it
should not replace deterministic policy and guardrail assertions.

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
