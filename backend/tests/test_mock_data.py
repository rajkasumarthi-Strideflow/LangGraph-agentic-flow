from app.tools.mock_data import (
    CURRENT_LAPTOP_POLICY_ID,
    DEPRECATED_LAPTOP_POLICY_ID,
    PRIMARY_CUSTOMER_ID,
    PRIMARY_ORDER_ID,
    PRIMARY_PRODUCT_ID,
    get_current_warranty_policy,
    get_customer,
    get_deprecated_warranty_policy,
    get_inventory_item,
    get_order,
    get_product,
)


def test_primary_customer_can_be_loaded() -> None:
    customer = get_customer(PRIMARY_CUSTOMER_ID)

    assert customer is not None
    assert customer.customer_id == PRIMARY_CUSTOMER_ID
    assert customer.region == "US"


def test_primary_order_can_be_loaded_and_is_delivered() -> None:
    order = get_order(PRIMARY_ORDER_ID)

    assert order is not None
    assert order.order_status == "delivered"
    assert order.customer_id == PRIMARY_CUSTOMER_ID
    assert order.product_id == PRIMARY_PRODUCT_ID


def test_primary_product_can_be_loaded_and_is_laptop() -> None:
    product = get_product(PRIMARY_PRODUCT_ID)

    assert product is not None
    assert product.product_family == "laptop"


def test_current_warranty_policy_can_be_loaded() -> None:
    policy = get_current_warranty_policy(product_family="laptop", region="US")

    assert policy is not None
    assert policy.policy_id == CURRENT_LAPTOP_POLICY_ID
    assert policy.status == "current"


def test_deprecated_warranty_policy_can_be_loaded() -> None:
    policy = get_deprecated_warranty_policy(DEPRECATED_LAPTOP_POLICY_ID)

    assert policy is not None
    assert policy.status == "deprecated"
    assert policy.replacement_policy_id == CURRENT_LAPTOP_POLICY_ID


def test_current_policy_excludes_accidental_damage_and_cracked_screens() -> None:
    policy = get_current_warranty_policy(product_family="laptop", region="US")

    assert policy is not None
    exclusions = " ".join(policy.excluded_conditions).lower()
    assert "accidental damage" in exclusions
    assert "cracked screens" in exclusions
    assert "drops" in exclusions
    assert "impact" in exclusions


def test_deprecated_policy_conflicts_with_current_policy() -> None:
    current_policy = get_current_warranty_policy(product_family="laptop", region="US")
    deprecated_policy = get_deprecated_warranty_policy(DEPRECATED_LAPTOP_POLICY_ID)

    assert current_policy is not None
    assert deprecated_policy is not None
    current_exclusions = " ".join(current_policy.excluded_conditions).lower()
    deprecated_coverage = " ".join(deprecated_policy.covered_conditions).lower()
    assert "cracked screens" in current_exclusions
    assert "cracked laptop screens may be covered" in deprecated_coverage


def test_inventory_item_can_be_loaded() -> None:
    inventory_item = get_inventory_item(PRIMARY_PRODUCT_ID)

    assert inventory_item is not None
    assert inventory_item.product_id == PRIMARY_PRODUCT_ID
    assert inventory_item.status == "available"
