from datetime import date
from typing import Any

from app.tools.mock_data import (
    get_current_warranty_policy,
    get_customer,
    get_inventory_item,
    get_order,
    get_product,
    list_warranty_policies,
)

CAPSTONE_REFERENCE_DATE = date(2026, 5, 23)
ELIGIBILITY_STATUSES: set[str] = {
    "eligible",
    "not_eligible",
    "unknown",
    "human_review_required",
}


def _months_between(start_date: date, end_date: date) -> int:
    months = (end_date.year - start_date.year) * 12
    months += end_date.month - start_date.month
    if end_date.day < start_date.day:
        months -= 1
    return max(months, 0)


def _get_policy_by_id(policy_id: str):
    for policy in list_warranty_policies():
        if policy.policy_id == policy_id:
            return policy
    return None


def _policy_reference(policy_id: str, version: str) -> str:
    return f"{policy_id}#v{version}"


def verify_identity(customer_id: str) -> dict[str, Any]:
    customer = get_customer(customer_id)
    identity_verified = bool(customer and customer.identity_verified)

    return {
        "result_status": "success" if identity_verified else "not_found",
        "customer_id": customer_id,
        "identity_verified": identity_verified,
        "reason": None if identity_verified else "Customer was not found or verified.",
    }


def lookup_order(customer_id: str, order_id: str) -> dict[str, Any]:
    order = get_order(order_id)
    if order is None:
        return {
            "result_status": "not_found",
            "customer_id": customer_id,
            "order_id": order_id,
            "reason": "Order was not found.",
        }

    if order.customer_id != customer_id:
        return {
            "result_status": "authorization_error",
            "customer_id": customer_id,
            "order_id": order_id,
            "reason": "Order does not belong to the provided customer.",
        }

    product = get_product(order.product_id)
    if product is None:
        return {
            "result_status": "not_found",
            "customer_id": customer_id,
            "order_id": order_id,
            "reason": "Product for order was not found.",
        }

    age_start = order.delivery_date or order.purchase_date
    return {
        "result_status": "success",
        "order_id": order.order_id,
        "customer_id": order.customer_id,
        "product_id": order.product_id,
        "product_family": product.product_family,
        "order_status": order.order_status,
        "purchase_age_months": _months_between(age_start, CAPSTONE_REFERENCE_DATE),
    }


def retrieve_warranty_policy(product_family: str, region: str) -> dict[str, Any]:
    policy = get_current_warranty_policy(product_family=product_family, region=region)
    if policy is None:
        return {
            "result_status": "not_found",
            "product_family": product_family,
            "region": region,
            "reason": "Current warranty policy was not found.",
        }

    return {
        "result_status": "success",
        "policy_id": policy.policy_id,
        "version": policy.version,
        "status": policy.status,
        "policy_reference": _policy_reference(policy.policy_id, policy.version),
        "product_family": policy.product_family,
        "region": policy.region,
        "coverage_summary": " ".join(policy.covered_conditions),
        "exclusions_summary": " ".join(policy.excluded_conditions),
    }


def check_replacement_eligibility(
    customer_id: str,
    order_id: str,
    policy_id: str,
) -> dict[str, Any]:
    order = get_order(order_id)
    if order is None:
        return {
            "result_status": "not_found",
            "customer_id": customer_id,
            "order_id": order_id,
            "eligibility_status": "unknown",
            "reason": "Order was not found.",
        }

    if order.customer_id != customer_id:
        return {
            "result_status": "authorization_error",
            "customer_id": customer_id,
            "order_id": order_id,
            "eligibility_status": "unknown",
            "reason": "Order does not belong to the provided customer.",
        }

    product = get_product(order.product_id)
    if product is None:
        return {
            "result_status": "not_found",
            "customer_id": customer_id,
            "order_id": order_id,
            "eligibility_status": "unknown",
            "reason": "Product for order was not found.",
        }

    current_policy = get_current_warranty_policy(
        product_family=product.product_family,
        region=order.region,
    )
    requested_policy = _get_policy_by_id(policy_id)
    if current_policy is None or requested_policy is None:
        return {
            "result_status": "requires_human_review",
            "customer_id": customer_id,
            "order_id": order_id,
            "product_id": product.product_id,
            "eligibility_status": "human_review_required",
            "reason": "Policy was not found and must be reviewed by a human.",
        }

    policy_reference = _policy_reference(current_policy.policy_id, current_policy.version)
    if policy_id != current_policy.policy_id or requested_policy.status != "current":
        return {
            "result_status": "requires_human_review",
            "customer_id": customer_id,
            "order_id": order_id,
            "product_id": product.product_id,
            "eligibility_status": "human_review_required",
            "policy_reference": policy_reference,
            "policy_version": current_policy.version,
            "reason": "Requested policy is not the current policy.",
        }

    if order.order_status != "delivered":
        return {
            "result_status": "success",
            "customer_id": customer_id,
            "order_id": order_id,
            "product_id": product.product_id,
            "eligibility_status": "not_eligible",
            "policy_reference": policy_reference,
            "policy_version": current_policy.version,
            "reason": "Order must be delivered before replacement eligibility can be approved.",
        }

    return {
        "result_status": "success",
        "customer_id": customer_id,
        "order_id": order_id,
        "product_id": product.product_id,
        "eligibility_status": "not_eligible",
        "policy_reference": policy_reference,
        "policy_version": current_policy.version,
        "reason": (
            "Accidental damage and cracked screens caused by drops, impact, or "
            "accidental damage are excluded by the current warranty policy."
        ),
    }


def check_inventory_availability(product_id: str) -> dict[str, Any]:
    inventory_item = get_inventory_item(product_id)
    if inventory_item is None:
        return {
            "result_status": "not_found",
            "product_id": product_id,
            "inventory_available": False,
            "inventory_status": "unavailable",
            "available_quantity": 0,
            "reason": "Inventory item was not found.",
        }

    inventory_available = (
        inventory_item.status == "available" and inventory_item.quantity_available > 0
    )
    return {
        "result_status": "success",
        "product_id": product_id,
        "inventory_available": inventory_available,
        "inventory_status": inventory_item.status,
        "available_quantity": inventory_item.quantity_available,
    }


def create_replacement_request(
    customer_id: str,
    order_id: str,
    product_id: str,
    eligibility_status: str,
    inventory_available: bool,
) -> dict[str, Any]:
    if eligibility_status not in ELIGIBILITY_STATUSES:
        return {
            "result_status": "validation_error",
            "replacement_status": "not_created",
            "customer_id": customer_id,
            "order_id": order_id,
            "product_id": product_id,
            "reason": "Eligibility status is not recognized.",
        }

    if eligibility_status != "eligible":
        return {
            "result_status": "blocked_by_guardrail",
            "replacement_status": "not_created",
            "customer_id": customer_id,
            "order_id": order_id,
            "product_id": product_id,
            "reason": "Replacement request cannot be created unless eligibility is approved.",
        }

    if not inventory_available:
        return {
            "result_status": "blocked_by_guardrail",
            "replacement_status": "not_created",
            "customer_id": customer_id,
            "order_id": order_id,
            "product_id": product_id,
            "reason": "Replacement request cannot be created without available inventory.",
        }

    return {
        "result_status": "success",
        "replacement_request_id": f"rr_{customer_id}_{order_id}_{product_id}",
        "replacement_status": "created",
        "customer_id": customer_id,
        "order_id": order_id,
        "product_id": product_id,
    }


def escalate_to_human(customer_id: str, order_id: str, reason: str) -> dict[str, Any]:
    return {
        "result_status": "success",
        "escalation_id": f"esc_{customer_id}_{order_id}",
        "escalation_status": "open",
        "reason": reason,
        "customer_id": customer_id,
        "order_id": order_id,
    }


def generate_customer_response(
    eligibility_status: str,
    replacement_request_id: str | None,
    escalation_id: str | None,
    reason: str,
) -> dict[str, Any]:
    if replacement_request_id:
        return {
            "result_status": "success",
            "response_type": "replacement_created",
            "customer_response": (
                "Your replacement request has been created. "
                f"Reference ID: {replacement_request_id}."
            ),
        }

    if escalation_id:
        return {
            "result_status": "success",
            "response_type": "human_review",
            "customer_response": (
                "Your case has been routed for human review. "
                f"Escalation ID: {escalation_id}. Reason: {reason}"
            ),
        }

    if eligibility_status == "not_eligible":
        return {
            "result_status": "success",
            "response_type": "not_eligible",
            "customer_response": (
                "Based on the current warranty policy, this item is not "
                f"automatically eligible for replacement. Reason: {reason}"
            ),
        }

    return {
        "result_status": "success",
        "response_type": "informational",
        "customer_response": reason,
    }
