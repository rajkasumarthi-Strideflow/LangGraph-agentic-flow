from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


OrderStatus = Literal["delivered", "processing", "cancelled", "returned"]
PolicyStatus = Literal["current", "deprecated", "draft"]
EligibilityStatus = Literal[
    "eligible",
    "not_eligible",
    "unknown",
    "human_review_required",
]
InventoryStatus = Literal["available", "unavailable", "backorder"]
ReplacementStatus = Literal["created", "pending_review", "rejected", "not_created"]
EscalationStatus = Literal["open", "resolved", "cancelled"]


class Customer(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    region: str
    identity_verified: bool = False


class Product(BaseModel):
    product_id: str
    name: str
    product_family: str
    sku: str
    replacement_product_id: str | None = None


class Order(BaseModel):
    order_id: str
    customer_id: str
    product_id: str
    order_status: OrderStatus
    purchase_date: date
    delivery_date: date | None = None
    region: str


class WarrantyPolicy(BaseModel):
    policy_id: str
    version: str
    title: str
    status: PolicyStatus
    audience: str
    product_family: str
    region: str
    effective_date: date
    expired_date: date | None = None
    replacement_policy_id: str | None = None
    standard_warranty_months: int
    covered_conditions: list[str] = Field(default_factory=list)
    excluded_conditions: list[str] = Field(default_factory=list)
    replacement_requirements: list[str] = Field(default_factory=list)
    source_summary: str


class InventoryItem(BaseModel):
    inventory_id: str
    product_id: str
    sku: str
    status: InventoryStatus
    quantity_available: int
    warehouse_region: str


class ReplacementRequest(BaseModel):
    request_id: str
    customer_id: str
    order_id: str
    product_id: str
    issue_description: str
    eligibility_status: EligibilityStatus
    replacement_status: ReplacementStatus
    created_at: date
    policy_id: str | None = None
    decision_reason: str | None = None


class HumanEscalation(BaseModel):
    escalation_id: str
    customer_id: str
    order_id: str | None = None
    request_id: str | None = None
    status: EscalationStatus
    reason: str
    created_at: date
    resolved_at: date | None = None
