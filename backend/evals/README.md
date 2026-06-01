# DecisionTrace AI Local Evaluations

This folder contains the Step 28A local golden-scenario evaluation pipeline and
the optional Step 30A LangSmith dataset/experiment bridge.

The pipeline validates the control model with deterministic assertions. Local
pytest evaluations remain the source of truth for control-model validation.
LangSmith experiments are optional and are used to track evaluation runs and
compare versions over time. LLM-as-judge can be added later for communication
quality, tone, and faithfulness checks, but it should not replace deterministic
policy and guardrail assertions.

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

## Optional LangSmith Evaluation

Step 30A adds `backend/evals/langsmith_export.py`, a manually invoked bridge from
the local golden scenarios to LangSmith datasets and experiments.

This is different from LangSmith tracing:

- Tracing captures how intake, workflow, tools, and LLM drafting executed.
- Evaluation measures whether the behavior met expected deterministic criteria.

The LangSmith integration is optional. The FastAPI app and regular pytest suite
run normally without `LANGSMITH_API_KEY`.

Required environment when exporting or running experiments:

```bash
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=decisiontrace-phase2
LANGSMITH_EVALUATION_DATASET=decisiontrace-phase2-golden-scenarios
LANGSMITH_EVALUATION_EXPERIMENT_PREFIX=decisiontrace-phase2
```

Manual commands:

```bash
cd backend
source .venv/bin/activate

python -m evals.langsmith_export --sync-dataset
python -m evals.langsmith_export --run-experiment
```

Dataset examples include:

- `business_scenario`
- `business_expectation`
- `control_model_expectation`
- deterministic `expected` assertions

The experiment target runs the same local deterministic scenario logic used by
`evals.runner`. It does not call OpenAI, does not require Railway, and does not
replace local pytest evaluation.
