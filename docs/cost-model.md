# WarrantyWise Cost Model v1

Cost modeling is part of enterprise agentic AI architecture. A production agent is not only an LLM prompt with tools; it is a workflow that consumes infrastructure, tool/API calls, retrieval, database writes, audit logging, observability, human review, and maintenance.

Phase 1 does not use real LLM calls yet, so token costs are documented as future/estimated costs rather than measured costs. Current Phase 1 cost drivers include app hosting, database persistence, API/tool execution, audit storage, and human review simulation.

## Cost Modeling Framework

### Layer 1: Core Consumption

- LLM input/output tokens
- Prompt/context size
- Tool/action invocations
- API calls
- Reasoning loop tax
- Retrieved context tokens once LLM/RAG is added

### Layer 2: Architectural Overhead

- Policy retrieval infrastructure
- Vector DB / embeddings once RAG is added
- Database writes
- Audit events
- Observability/tracing
- Guardrail checks
- Evaluation runs
- Storage and retention

### Layer 3: Business TCO

- Human review and escalation cost
- Support operations time
- Partner implementation hours
- Maintenance and drift
- Prompt tuning
- Evaluation harness updates
- Broken API/integration fixes
- Incident response

## WarrantyWise Phase 1 Cost Drivers

| Workflow Step | Cost Driver | Cost Layer | Notes |
| --- | --- | --- | --- |
| Customer request submitted | HTTP request and frontend interaction | Core Consumption | Browser UI calls FastAPI. |
| FastAPI request handling | App compute | Core Consumption | Request validation, response serialization, routing. |
| LangGraph workflow execution | Workflow orchestration | Core Consumption | Deterministic state transitions, no LLM loop yet. |
| `verify_identity` tool | Tool invocation | Core Consumption | Mock lookup now; future integration may call identity service. |
| `lookup_order` tool | Tool invocation | Core Consumption | Mock lookup now; future order API cost may apply. |
| `retrieve_warranty_policy` tool | Policy retrieval | Architectural Overhead | Mock policy retrieval now; future RAG/vector cost may apply. |
| `check_replacement_eligibility` tool | Decision support | Core Consumption | Deterministic policy eligibility logic. |
| `check_inventory_availability` tool | Tool invocation | Core Consumption | Mock inventory now; future inventory API cost may apply. |
| `guardrail_check` node | Guardrail execution | Architectural Overhead | Prevents unsafe replacement creation. |
| `create_replacement_request` tool | Controlled write/action | Core Consumption | Runs only when guardrails allow. |
| `escalate_to_human` tool | Escalation path | Business TCO | Future real queue/case routing adds operational cost. |
| `generate_customer_response` tool | Response generation | Core Consumption | Deterministic Phase 1; future LLM drafting may add token cost. |
| `workflow_runs` database write | Persistence | Architectural Overhead | Stores final workflow state. |
| `audit_events` database writes | Audit persistence | Architectural Overhead | One event per meaningful workflow step. |
| `human_reviews` database write | Human review persistence | Business TCO | Stores simulated reviewer decisions. |
| Railway app hosting | Compute hosting | Architectural Overhead | Container hosting for FastAPI and static frontend. |
| Railway Postgres | Managed database | Architectural Overhead | Stores workflow, audit, and review tables. |
| Future LLM response drafting | Token consumption | Core Consumption | Not implemented in Phase 1. |
| Future RAG/vector retrieval | Embeddings, vector search, context tokens | Architectural Overhead | Future policy grounding at scale. |
| Future Langfuse/LangSmith tracing | Trace storage and observability | Architectural Overhead | Future production observability. |
| Future Ragas evaluation | Evaluation runs | Architectural Overhead | Future retrieval/answer quality measurement. |

## Example Cost per Interaction Formula

```text
cost_per_interaction =
  LLM token cost
  + tool/API invocation cost
  + retrieval/index cost
  + database/audit storage cost
  + observability cost
  + human review cost allocation
  + infrastructure allocation
```

In Phase 1, LLM token cost is zero because no real LLM call has been added yet. The dominant costs are hosting, database persistence, workflow/API execution, and audit writes.

## Cost per Outcome

Cost per interaction is not enough because different outcomes have different business value and operational cost.

Track:

- Cost per resolved case
- Cost per escalated case
- Cost per blocked/denied case
- Cost per failed workflow
- Cost per human-reviewed case

A blocked cracked-screen case may be cheaper operationally than a replacement flow, but it is still valuable because it prevents unsupported replacement cost and gives the customer a policy-grounded response.

## Reasoning Loop Tax

Multi-step ReAct-style agents can repeatedly resend system prompts, tool definitions, chat history, and retrieved context. A five-step loop may cost much more than a two-step loop because context is repeatedly passed back to the LLM.

WarrantyWise Phase 1 avoids this by using deterministic LangGraph routing. Future LLM use should include max tool-call limits, max reasoning-loop limits, and fallback behavior.

## Prompt and Context Bloat

Large system prompts, tool schemas, policy chunks, Salesforce metadata, object schemas, and conversation history can create a high fixed token cost.

Context bloat should be managed through:

- Structured workflow state
- Summary memory
- Retrieved chunk limits
- Scoped tool definitions
- Avoiding full raw history when a state summary is enough

## Prompt Caching Pattern

Prompt caching is useful when stable prompt prefixes are repeatedly reused. This is a future enhancement once real LLM calls are added.

Stable content examples:

- System prompt
- Tool definitions
- Output schema
- Safety instructions
- Static policy response rules

Design guidance:

- Keep stable prompt content at the beginning.
- Separate static prompt prefix from dynamic state/context.
- Avoid unnecessary changes to the cached prefix.
- Track cached tokens when the provider supports it.

## Semantic Caching Pattern

Semantic caching can reduce repeated cost for common warranty questions and responses when policy and context are stable.

Use for repetitive low-risk policy explanations. Do not use when customer-specific facts, order status, eligibility, or policy version differ. Always include cache invalidation rules when policy changes.

## Dynamic Model Selection / Model Routing Pattern

Use the cheapest model that can safely meet the quality, risk, and business outcome requirement; escalate to a stronger model when risk, ambiguity, or value justifies the cost.

| Criteria | Low-Cost Model Appropriate When | Frontier Model Appropriate When |
| --- | --- | --- |
| Task complexity | Intent classification, simple formatting, structured summaries | Complex exception reasoning or multi-step ambiguity |
| Risk tier | Low-risk informational response | High-impact eligibility or customer commitment |
| Ambiguity | Clear customer intent and known state | Conflicting facts or unclear customer scenario |
| Policy impact | Policy answer is straightforward | Policy interpretation is nuanced or conflicting |
| Tool/action risk | No write/action tool is triggered | Tool may create, approve, refund, replace, or escalate |
| Confidence score | High confidence from deterministic state | Low confidence or uncertain retrieval |
| Failure/retry signals | No prior failure | Repeated failures, tool errors, or fallback path |
| Customer/business value | Low-value routine interaction | High-value customer or high-cost decision |
| Regulatory/compliance sensitivity | No sensitive compliance implications | Regulated, contractual, or dispute-prone context |
| Need for nuanced communication | Simple response formatting | Sensitive customer explanation or executive summary |

Examples:

- Low-cost model: intent classification, simple response formatting, summarization of structured state
- Frontier model: complex exception reasoning, conflicting policy interpretation, high-value customer escalation summary, ambiguous multi-step customer scenario

## State and Memory Cost Controls

Conversation memory should support dialogue continuity. Workflow state should hold execution control facts. Long-term memory should store only durable, governed preferences.

Do not resend raw full history when structured state or summaries are enough. Do not store temporary workflow facts in long-term memory. Use summarized state/history to reduce token growth in long sessions.

## Execution Hard Caps

Recommended caps:

- Maximum workflow steps
- Maximum tool calls
- Maximum retries
- Maximum retrieved chunks
- Timeout thresholds
- Circuit breaker for failing tools
- Escalation instead of repeated retries

## Audit and Observability Cost Controls

Auditability is required but not free. Every audit event creates database writes and storage. Observability tools add trace and storage costs.

Cost controls include:

- Safe payload minimization
- Retention policy
- Sampling where appropriate
- Avoiding sensitive raw payloads
- Recording references and summaries instead of full payloads

## Human Review Cost Model

HITL is a business TCO driver.

```text
human_review_cost = average_review_minutes × loaded_hourly_rate / 60
```

Track escalation rate and approval/rejection rate. A high escalation rate may indicate poor automation, policy ambiguity, weak retrieval, unclear guardrails, or missing integrations.

## WarrantyWise Cost-Control Blueprint

| Step | Optimization Lever | Technical Mechanism | Financial Impact |
| --- | --- | --- | --- |
| Common policy questions | Semantic caching | Cache stable low-risk policy explanations | Reduces repeated LLM/RAG cost |
| Reused prompt structure | Prompt caching | Stable prompt prefix for system/tools/schema | Reduces repeated token cost |
| Response drafting | Dynamic model routing | Choose model by risk, ambiguity, and value | Avoids overusing frontier models |
| Long sessions | State/history summarization | Summarize dialogue and use structured state | Reduces context growth |
| Policy grounding | Retrieved chunk limits | Cap retrieved policy chunks | Controls retrieval and token cost |
| Workflow execution | Execution hard caps | Max steps, retries, and timeouts | Prevents runaway workflows |
| Tool usage | Tool-call limits | Cap tool invocations per run | Reduces API and loop cost |
| Replacement decisions | Guardrail-first design | Deterministic checks before write/action | Prevents unsupported business cost |
| Escalations | Human escalation sampling/review | Track escalation quality and outcomes | Controls support operations TCO |
| Audit logging | Audit payload minimization | Store safe summaries and references | Reduces storage and compliance risk |

## Sample Interview Q&A

### How would you estimate cost per interaction?

Add token cost, tool/API invocation cost, retrieval/index cost, database/audit storage, observability, human review allocation, and infrastructure allocation.

### Why are database writes and audit events cost drivers?

Every persisted workflow, audit event, and review record consumes database write capacity, storage, backup, and retention cost.

### How do you prevent runaway agent costs?

Use deterministic routing where possible, max workflow steps, max tool calls, retry limits, timeouts, circuit breakers, and escalation instead of repeated retries.

### When would you use a low-cost model instead of a frontier model?

Use a low-cost model for intent classification, simple formatting, and summarizing structured state when risk and ambiguity are low.

### When would you switch to a frontier model?

Switch when the case is ambiguous, high-value, compliance-sensitive, policy-conflicted, or requires nuanced communication.

### How do human escalations affect cost?

Escalations add loaded labor cost and operational delay. Track escalation rate, average review time, and approval/rejection outcomes.

### How does LangGraph help control cost?

LangGraph makes routing explicit, reduces unnecessary reasoning loops, supports deterministic decisions, and provides clear points for caps and fallbacks.

### How would prompt caching help?

It reduces repeated cost for stable prompt prefixes such as system instructions, tool schemas, output schemas, and safety rules.

### How would semantic caching help?

It avoids repeated generation for common low-risk policy explanations when policy version and context are stable.

### Why is cost per resolved case more useful than cost per interaction?

Cost per resolved case ties spend to business outcomes. A cheap interaction that fails or escalates unnecessarily may cost more end-to-end than a slightly more expensive resolved case.

## Phase 1 vs Future Cost Model

### Phase 1

- No real LLM calls
- Deterministic workflow
- Mocked tools
- Database persistence
- Railway app and Postgres hosting
- Audit storage

### Future

- LLM token tracking
- Cached token tracking
- Real RAG retrieval cost
- Langfuse/LangSmith tracing cost
- Ragas evaluation cost
- Dynamic model routing
- Semantic cache hit rate
- Cost per resolved/escalated/failed case
