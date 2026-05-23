from datetime import date

from app.models.domain import (
    Customer,
    InventoryItem,
    Order,
    Product,
    WarrantyPolicy,
)

PRIMARY_CUSTOMER_ID = "cust_primary_001"
PRIMARY_PRODUCT_ID = "prod_laptop_001"
PRIMARY_ORDER_ID = "ord_laptop_001"
CURRENT_LAPTOP_POLICY_ID = "pol_laptop_us_current_v2"
DEPRECATED_LAPTOP_POLICY_ID = "pol_laptop_us_faq_v1"


CUSTOMERS: dict[str, Customer] = {
    PRIMARY_CUSTOMER_ID: Customer(
        customer_id=PRIMARY_CUSTOMER_ID,
        first_name="Jordan",
        last_name="Miller",
        email="jordan.miller@example.com",
        phone="+1-555-0109",
        region="US",
        identity_verified=True,
    )
}

PRODUCTS: dict[str, Product] = {
    PRIMARY_PRODUCT_ID: Product(
        product_id=PRIMARY_PRODUCT_ID,
        name="WarrantyWise ProBook 14",
        product_family="laptop",
        sku="WW-LAPTOP-PROBOOK-14",
        replacement_product_id="prod_laptop_replacement_001",
    )
}

ORDERS: dict[str, Order] = {
    PRIMARY_ORDER_ID: Order(
        order_id=PRIMARY_ORDER_ID,
        customer_id=PRIMARY_CUSTOMER_ID,
        product_id=PRIMARY_PRODUCT_ID,
        order_status="delivered",
        purchase_date=date(2025, 8, 16),
        delivery_date=date(2025, 8, 23),
        region="US",
    )
}

WARRANTY_POLICIES: dict[str, WarrantyPolicy] = {
    CURRENT_LAPTOP_POLICY_ID: WarrantyPolicy(
        policy_id=CURRENT_LAPTOP_POLICY_ID,
        version="2.0",
        title="US Laptop Limited Warranty Policy",
        status="current",
        audience="customer_facing",
        product_family="laptop",
        region="US",
        effective_date=date(2026, 1, 1),
        standard_warranty_months=12,
        covered_conditions=[
            "Manufacturing defects may be covered within the standard warranty window.",
            "Hardware failures caused by defects in materials or workmanship may be covered.",
        ],
        excluded_conditions=[
            "Accidental damage is excluded from standard warranty coverage.",
            "Cracked screens caused by drops, impact, or accidental damage are excluded.",
            "Cosmetic damage, misuse, liquid damage, and unauthorized repairs are excluded.",
        ],
        replacement_requirements=[
            "Customer identity verification is required.",
            "Customer must own the order associated with the product.",
            "Order status must be delivered.",
            "The issue must be eligible under the current warranty policy.",
            "Replacement inventory must be available.",
        ],
        source_summary=(
            "Standard laptop warranty runs for 12 months from purchase or delivery. "
            "Manufacturing defects may be covered, but accidental damage and cracked "
            "screens caused by drops, impact, or accidental damage are excluded."
        ),
    ),
    DEPRECATED_LAPTOP_POLICY_ID: WarrantyPolicy(
        policy_id=DEPRECATED_LAPTOP_POLICY_ID,
        version="1.0",
        title="Legacy Laptop Warranty FAQ",
        status="deprecated",
        audience="customer_facing",
        product_family="laptop",
        region="US",
        effective_date=date(2024, 1, 1),
        expired_date=date(2025, 12, 31),
        replacement_policy_id=CURRENT_LAPTOP_POLICY_ID,
        standard_warranty_months=12,
        covered_conditions=[
            "Legacy FAQ suggested some cracked laptop screens may be covered after review.",
            "Manufacturing defects may be covered within the standard warranty window.",
        ],
        excluded_conditions=[
            "Intentional damage and unauthorized repairs are excluded.",
        ],
        replacement_requirements=[
            "Customer identity verification is required.",
            "Customer must own the order associated with the product.",
            "Order status must be delivered.",
        ],
        source_summary=(
            "Deprecated FAQ content conflicts with the current policy by suggesting "
            "that cracked screens may be covered. This policy is expired and should "
            "be superseded by the current laptop warranty policy."
        ),
    ),
}

INVENTORY_ITEMS: dict[str, InventoryItem] = {
    PRIMARY_PRODUCT_ID: InventoryItem(
        inventory_id="inv_laptop_replacement_001",
        product_id=PRIMARY_PRODUCT_ID,
        sku="WW-LAPTOP-PROBOOK-14-R",
        status="available",
        quantity_available=5,
        warehouse_region="US",
    )
}


def get_customer(customer_id: str) -> Customer | None:
    return CUSTOMERS.get(customer_id)


def get_order(order_id: str) -> Order | None:
    return ORDERS.get(order_id)


def get_product(product_id: str) -> Product | None:
    return PRODUCTS.get(product_id)


def get_current_warranty_policy(
    product_family: str,
    region: str,
) -> WarrantyPolicy | None:
    for policy in WARRANTY_POLICIES.values():
        if (
            policy.status == "current"
            and policy.product_family == product_family
            and policy.region == region
        ):
            return policy
    return None


def get_deprecated_warranty_policy(policy_id: str) -> WarrantyPolicy | None:
    policy = WARRANTY_POLICIES.get(policy_id)
    if policy and policy.status == "deprecated":
        return policy
    return None


def get_inventory_item(product_id: str) -> InventoryItem | None:
    return INVENTORY_ITEMS.get(product_id)


def list_warranty_policies() -> list[WarrantyPolicy]:
    return list(WARRANTY_POLICIES.values())
