from typing import TypedDict


class WarrantyWorkflowState(TypedDict):
    workflow_id: str
    correlation_id: str
    customer_request: str
    customer_id: str
    order_id: str
    product_id: str | None
    product_family: str | None
    identity_verified: bool
    customer_authorized: bool
    order_retrieved: bool
    order_status: str | None
    purchase_age_months: int | None
    policy_id: str | None
    policy_reference: str | None
    policy_version: str | None
    eligibility_status: str | None
    eligibility_reason: str | None
    inventory_available: bool | None
    inventory_status: str | None
    replacement_request_id: str | None
    replacement_status: str | None
    escalation_id: str | None
    escalation_required: bool
    escalation_reason: str | None
    guardrail_decision: str | None
    customer_response: str | None
    response_type: str | None
    llm_drafting_status: str | None
    llm_customer_response: str | None
    llm_model_name: str | None
    llm_input_tokens: int | None
    llm_output_tokens: int | None
    llm_total_tokens: int | None
    llm_cached_tokens: int | None
    llm_validation_status: str | None
    llm_validation_errors: list[str] | None
    final_response_source: str | None
    error_category: str | None
    workflow_status: str
