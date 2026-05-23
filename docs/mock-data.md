# Mock Data Foundation

## Purpose

The synthetic mock data provides a stable in-memory business domain for the WarrantyWise capstone. It gives later tools and workflow nodes predictable customers, products, orders, policies, and inventory records without requiring a database or external service integration.

This layer is intentionally small and deterministic. It is designed to support warranty replacement workflow development while keeping Step 2 focused on domain modeling and testable fixtures.

## Primary Customer Scenario

The primary scenario prepares the system for this customer request:

> My laptop screen cracked after 9 months. Can I get a replacement?

The mock data includes one verified US customer, one laptop product, and one delivered laptop order. The order was delivered on 2025-08-23, which is nine months before the capstone reference date of 2026-05-23.

## Current Warranty Policy

The current customer-facing US laptop warranty policy states that the standard warranty window is 12 months from purchase or delivery. Manufacturing defects may be covered during that window.

The current policy excludes accidental damage. It also explicitly excludes cracked screens caused by drops, impact, or accidental damage. Because the primary customer request describes a cracked screen, later eligibility logic should not treat the issue as automatically covered by the standard warranty.

Replacement also requires identity verification, order ownership, delivered order status, policy eligibility, and available replacement inventory.

## Deprecated Warranty Policy

The mock data also includes an older deprecated laptop warranty FAQ. It intentionally conflicts with the current policy by suggesting that cracked laptop screens may be covered after review.

That deprecated policy has an older version, expired dates, `status=deprecated`, and a `replacement_policy_id` that points to the current policy. It exists so future retrieval and reasoning tests can verify that stale sources are detected and ranked below the active policy.

## Future Testing Support

These fixtures support later development of RAG, source priority, guardrails, and auditability:

- RAG tests can retrieve both current and deprecated warranty sources.
- Source-priority tests can verify that current policy wins over stale FAQ content.
- Guardrail tests can require human review when policy conflicts or uncertainty appear.
- Audit tests can record which customer, order, product, policy, and inventory records were used to make a decision.

No database persistence, LangGraph workflow, or external integration is included in this step.
