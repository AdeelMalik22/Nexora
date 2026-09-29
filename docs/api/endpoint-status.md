# Endpoint Coverage Status

The current API surface is covered by endpoint tests for authentication, tenant context, health, catalog, inventory, sales, payments, returns, shifts, and audit access.

## Core endpoints

| Area | Endpoints |
|---|---|
| Health | `/health/live/`, `/health/ready/` |
| Authentication | `/api/v1/auth/signup/`, `/login/`, `/refresh/` |
| Devices | `/api/v1/auth/devices/`, `/devices/list/`, `/devices/{id}/approve/`, `/devices/{id}/revoke/` |
| Staff | `/api/v1/auth/memberships/`, `/memberships/{id}/activate/`, `/memberships/{id}/deactivate/`, `/invitations/`, `/invitations/accept/` |
| Roles and audit | `/api/v1/auth/roles/`, `/api/v1/audit/` |
| Catalog | `/api/v1/catalog/categories/`, `/units/`, `/tax-categories/`, `/products/`, `/variants/`, `/barcodes/`, `/price-lists/`, `/prices/` |
| Inventory | `/api/v1/inventory/suppliers/`, `/stock/`, `/movements/`, `/purchases/`, `/purchases/receive/`, `/transfers/`, `/counts/` |
| Sales | `/api/v1/sales/carts/`, `/carts/{id}/items/`, `/carts/{id}/finalize/`, `/invoices/`, `/returns/`, `/shifts/`, `/shifts/{id}/close/` |
| Payments | `/api/v1/payments/methods/` |

Endpoint tests must verify authentication, tenant headers, permissions, successful responses, validation errors, and important side effects. New endpoints must be added to this document and covered by tests in the same pull request.
