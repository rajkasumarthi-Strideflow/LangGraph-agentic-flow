# DecisionTrace AI Architecture Diagrams

These diagrams show the Phase 1 architecture and planned future-state extensions for DecisionTrace AI, an enterprise-grade agentic decision workflow platform. The diagrams currently show the warranty replacement reference workflow implemented in Phase 1. Phase 1 is deterministic and production-aware: FastAPI serves the frontend and API, LangGraph orchestrates the workflow, governed tools execute bounded actions, SQLAlchemy persists state and audit records, and Railway provides the deployment target.

## Diagram 1: System Architecture

```mermaid
flowchart TD
    User["User / Browser UI"] --> Frontend

    subgraph RailwayApp["Railway App Service"]
        Frontend["Static Frontend<br/>HTML / CSS / JavaScript"]
        API["FastAPI API Layer"]
        Graph["LangGraph Warranty Reference Workflow"]
        Tools["Governed Mock Tools"]
        Guardrails["Deterministic Guardrails"]
        Persistence["SQLAlchemy Persistence Layer"]
    end

    Frontend --> API
    API --> Graph
    Graph --> Tools
    Graph --> Guardrails
    Graph --> Persistence

    subgraph DB["Railway Postgres"]
        WorkflowRuns["workflow_runs"]
        AuditEvents["audit_events"]
        HumanReviews["human_reviews"]
    end

    Persistence --> WorkflowRuns
    Persistence --> AuditEvents
    Persistence --> HumanReviews
```

## Diagram 2: LangGraph Workflow

```mermaid
flowchart TD
    Start([Start workflow]) --> Verify["verify_identity"]
    Verify --> IdentityDecision{"Identity verified?"}
    IdentityDecision -- "No" --> Escalate["escalate_to_human"]
    IdentityDecision -- "Yes" --> Lookup["lookup_order"]

    Lookup --> OrderDecision{"Order retrieved<br/>and authorized?"}
    OrderDecision -- "No" --> Escalate
    OrderDecision -- "Yes" --> Policy["retrieve_warranty_policy"]

    Policy --> PolicyDecision{"Policy reference exists?"}
    PolicyDecision -- "No" --> Escalate
    PolicyDecision -- "Yes" --> Eligibility["check_replacement_eligibility"]

    Eligibility --> EligibilityDecision{"Eligibility status"}
    EligibilityDecision -- "not_eligible" --> Guardrail["guardrail_check"]
    EligibilityDecision -- "unknown / human_review_required" --> Escalate
    EligibilityDecision -- "eligible" --> Inventory["check_inventory_availability"]

    Inventory --> InventoryDecision{"Inventory available?"}
    InventoryDecision -- "No" --> Escalate
    InventoryDecision -- "Yes" --> Guardrail

    Guardrail --> GuardrailDecision{"Guardrail decision"}
    GuardrailDecision -- "allow" --> Replacement["create_replacement_request"]
    GuardrailDecision -- "block" --> Response["generate_customer_response"]
    GuardrailDecision -- "escalate" --> Escalate

    Replacement --> Response
    Escalate --> Response
    Response --> End([End workflow])
```

## Diagram 3: Guardrail Decision Flow

```mermaid
flowchart TD
    Input["Workflow State"] --> C1{"identity_verified = true"}
    C1 -- "No" --> Escalate["Escalate"]
    C1 -- "Yes" --> C2{"customer_authorized = true"}
    C2 -- "No" --> Escalate
    C2 -- "Yes" --> C3{"order_retrieved = true"}
    C3 -- "No" --> Escalate
    C3 -- "Yes" --> C4{"order_status = delivered"}
    C4 -- "No" --> Escalate
    C4 -- "Yes" --> C5{"policy_reference exists"}
    C5 -- "No" --> Escalate
    C5 -- "Yes" --> C6{"eligibility_status"}

    C6 -- "not_eligible" --> Block["Block replacement creation"]
    C6 -- "unknown / conflict" --> Escalate
    C6 -- "eligible" --> C7{"inventory_available = true"}

    C7 -- "No" --> Escalate
    C7 -- "Yes" --> C8{"escalation_required = false"}
    C8 -- "No" --> Escalate
    C8 -- "Yes" --> Allow["Allow replacement creation"]

    Allow --> Create["create_replacement_request"]
    Block --> Response["generate_customer_response"]
    Escalate --> Human["escalate_to_human"]
```

## Diagram 4: Audit/Event Flow

```mermaid
flowchart TD
    Node["LangGraph node executes"] --> Result["Tool / decision result produced"]
    Result --> Logger["Audit logger creates AuditEvent"]
    Logger --> Table["audit_events table"]
    Table --> API["GET /api/workflows/{workflow_id}/audit"]
    API --> UI["Frontend audit timeline"]

    subgraph Events["Sample event types"]
        E1["workflow_started"]
        E2["policy_retrieved"]
        E3["eligibility_checked"]
        E4["guardrail_decision"]
        E5["replacement_request_created"]
        E6["human_escalation_created"]
        E7["customer_response_generated"]
        E8["workflow_completed"]
    end

    Logger --> E1
    Logger --> E2
    Logger --> E3
    Logger --> E4
    Logger --> E5
    Logger --> E6
    Logger --> E7
    Logger --> E8
```

## Diagram 5: Deployment Architecture

```mermaid
flowchart TD
    Repo["GitHub repo"] --> Build["Railway build<br/>Dockerfile"]
    Build --> Service["Railway FastAPI app service"]
    Domain["Public Railway domain"] --> Service
    Browser["Browser user"] --> Domain

    Service --> API["FastAPI API + static frontend"]
    Service --> Port["PORT environment variable"]
    Service --> DatabaseURL["DATABASE_URL reference variable"]

    DatabaseURL --> Postgres["Railway Postgres service"]
    API --> Postgres
```

## Diagram 6: Future-State Extension Architecture

```mermaid
flowchart TD
    Phase1["Phase 1 implemented core<br/>FastAPI + LangGraph + tools + OpenAI response drafting + persistence"] --> Future["Future-state extensions"]

    Future --> LLM["Natural language intake<br/>and drafting expansion"]
    Future --> Ragas["Ragas evaluation"]
    Future --> Observability["Langfuse / LangSmith observability"]
    Future --> CrewAI["CrewAI review crew"]
    Future --> MCP["MCP tools / resources / prompts"]
    Future --> A2A["A2A fulfillment delegation"]
    Future --> Interrupts["LangGraph interrupts<br/>true HITL pause/resume"]
    Future --> Agentforce["Agentforce mapping"]

    LLM --> Governance["Policy controls and cost limits"]
    Ragas --> Quality["Retrieval and answer quality checks"]
    Observability --> Traceability["Production traces and metrics"]
    CrewAI --> Review["Specialized review agents"]
    MCP --> Tooling["Standardized tool abstraction"]
    A2A --> Fulfillment["External fulfillment agents"]
    Interrupts --> HITL["Human approval workflow"]
    Agentforce --> Salesforce["Salesforce architecture alignment"]
```
