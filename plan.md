# Nexora Backend Plan

## 1. Product Direction

Nexora is a multi-tenant, offline-capable POS platform for small and medium businesses. A shared backend provides reliable billing, stock, payments, customers, reporting, notifications, and local compliance. Industry modules add workflows for pharmacy, grocery, restaurant, clothing, mobile shops, and salons or clinics.

The backend must make a small shop productive quickly while preserving enough separation to support multiple branches, local languages, local payment methods, tax integrations, and future service extraction.

### Product principles

- A shop can use only the modules it has enabled.
- Sales, payments, stock movements, and ledgers are auditable and mathematically correct.
- Offline clients can continue selling and synchronize safely later.
- Every tenant boundary is enforced in application code and the database.
- Domain rules live in services and policies, not in API views or frontend code.
- The first release proves one focused industry module before expanding to every industry.

## 2. Recommended Technical Stack

- **Language and framework:** Python, Django, Django REST Framework
- **API schema:** drf-spectacular, OpenAPI 3
- **Database:** PostgreSQL
- **Async work:** Celery with Redis as broker
- **Cache and rate limiting:** Redis
- **Authentication:** JWT access and refresh tokens, device registration, scoped device credentials
- **Storage:** S3-compatible object storage for logos, receipts, exports, and documents
- **Deployment:** Docker, Gunicorn, Nginx or managed ingress
- **Monitoring:** structured logs, Sentry, Prometheus-compatible metrics, alerting
- **CI/CD:** GitHub Actions, migration checks, immutable deploy artifacts

PostgreSQL is the system of record. Redis is disposable and must never be the only place where business data exists.

## 3. Repository Structure

The repository root is the backend project; there is no extra `backend/` directory.

```text
config/
  settings/
    base.py
    local.py
    test.py
    production.py
  urls.py
  asgi.py
  wsgi.py
  celery.py

apps/
  common/                  # shared primitives without business ownership
  accounts/                # users, roles, permissions, sessions, devices
  tenants/                 # shops, branches, plans, modules, settings
  catalog/                 # products, variants, units, prices, barcodes
  inventory/               # stock movements, purchasing, transfers, audits
  sales/                   # carts, invoices, returns, shifts, cash drawers
  payments/                # payment methods, gateways, reconciliation
  customers/               # customers, credit ledger, loyalty
  reporting/               # summaries, read models, exports
  notifications/           # templates, delivery, provider adapters
  synchronization/         # change log, cursors, push and pull operations
  taxation/                # tax rules, fiscal documents, local adapters
  subscriptions/           # Nexora plans, entitlements, billing
  integrations/            # webhooks and external contracts
  industry/
    pharmacy/
    grocery/
    restaurant/
    clothing/
    mobile_shop/
    salon_clinic/

tests/
  unit/
  integration/
  contract/
  security/
  sync/

docker/
  local/
  production/
docs/
  adr/
  api/
manage.py
```

### Module boundary rules

- Each app owns its models, migrations, services, policies, selectors, tasks, and API layer.
- An app may call another app through a public service or selector interface.
- An app must not import another app's models in business logic or write directly to another app's tables.
- Cross-module workflows use application services and domain events.
- `common` contains IDs, timestamps, money helpers, errors, and request context. It must not become a business-logic dumping ground.
- Industry modules depend on shared contracts; core modules do not depend on a specific industry module.

## 4. Domain Ownership

| Area | Owns | Main invariants |
|---|---|---|
| Accounts | users, roles, permissions, devices | access is revocable and auditable |
| Tenants | shops, branches, settings, enabled modules | every business record belongs to one shop |
| Catalog | products, variants, units, prices, barcodes | identifiers and prices are correctly scoped |
| Inventory | movements, balances, purchasing, transfers | stock changes only through movements |
| Sales | invoices, returns, shifts, cash drawers | finalized invoices are immutable |
| Payments | payments, gateway transactions, reconciliation | a payment is never silently duplicated or lost |
| Customers | profiles, credit ledger, loyalty | ledger entries are append-only |
| Sync | idempotency, change feed, cursors | retries and out-of-order delivery are safe |
| Taxation | tax rules and fiscal documents | tax calculation is reproducible |
| Reporting | read models and exports | freshness and scope are visible |
| Subscriptions | Nexora plans and entitlements | access follows plan and grace rules |

## 5. Multi-Tenancy and Access Control

- `Shop` is the tenant boundary; `Branch` belongs to a shop.
- Every tenant-owned table includes `shop_id`; branch-owned tables also include `branch_id`.
- UUIDs are used for primary keys and are safe for offline creation.
- UTC timestamps are stored; shop timezone is used for business dates and reports.
- Tenant context comes from the authenticated user, device, and selected branch. Client-supplied tenant IDs are never trusted.

### Enforcement layers

1. Request context establishes the current shop and branch.
2. Query managers require tenant context for normal queries.
3. Services validate shop and branch ownership before writes.
4. PostgreSQL Row-Level Security protects production tables.
5. Security tests attempt cross-shop reads, writes, exports, sync pulls, and object access.

Raw cross-tenant queries are available only to audited administrative jobs through an explicit `unscoped()` path.

Initial roles: Owner, Manager, Cashier, Stock Keeper, Accountant, and industry roles such as Pharmacist or Stylist. Permissions are explicit, for example `sales.void_invoice`, `catalog.change_price`, `inventory.adjust_stock`, and `reports.view_profit`. Sensitive operations can require manager approval.

## 6. Core Data and Financial Rules

### Identifiers and money

- Use UUID primary keys; clients may generate IDs for offline-created records.
- Use integer minor units for currency amounts where practical, with currency recorded explicitly.
- Use `Decimal` for weighted quantities and rates; never use floating point for money or stock calculations.
- Define rounding per currency and tax rule. Store calculated totals and their calculation inputs.
- Use `created_at`, `updated_at`, `deleted_at`, and, where needed, `business_date`.
- Never hard-delete financial, stock, payment, or audit records.

### Append-only facts

- Inventory is a journal of purchase, sale, return, transfer, adjustment, and opening-balance movements.
- Customer credit is an append-only ledger of charges, payments, refunds, adjustments, and reversals.
- Payments are immutable facts with explicit refund or reversal records.
- Audit logs record actor, device, request ID, action, object, before state, after state, and reason.

### Sales invariants

- Draft carts may change; finalized invoices cannot be edited.
- Corrections happen through returns, credit notes, refunds, or controlled reversals.
- Invoice creation is atomic across invoice, lines, taxes, stock movements, payment allocations, and sync acknowledgement.
- Split payments are separate allocations linked to one invoice.
- An invoice stores snapshots of product description, tax, price, discount, and unit.

## 7. Shared Modules

### Accounts and tenants

Models: `User`, `Role`, `Permission`, `Device`, `Shop`, `Branch`, `ShopModule`, `ShopSetting`, `Subscription`, `Entitlement`.

Features: owner signup, staff invitations, PIN login for authorized devices, device revocation, branch switching, plan limits, module enablement, timezone, currency, and tax settings.

### Catalog

Models: `Category`, `Product`, `ProductVariant`, `Unit`, `Barcode`, `PriceList`, `Price`, `TaxCategory`.

Features: barcode lookup, search, price history, purchase and selling units, variants, bulk import, soft deletion, and catalog snapshots for offline clients.

### Inventory and purchasing

Models: `StockMovement`, `StockBalance`, `Supplier`, `PurchaseOrder`, `PurchaseItem`, `StockTransfer`, `StockCount`, `StockAdjustment`.

`StockMovement` is the source of truth. `StockBalance` is a rebuildable projection. Every adjustment requires a reason and permission. Transfers have sent, received, and discrepancy states.

### Sales and cash

Models: `Cart`, `Invoice`, `InvoiceItem`, `InvoiceTax`, `Return`, `ReturnItem`, `CreditNote`, `Shift`, `CashDrawerEntry`.

Features: held carts, discounts, returns, exchanges, receipts, shift opening and closing, cash variance, invoice numbering, and offline invoice references.

### Payments

Models: `PaymentMethod`, `Payment`, `PaymentAllocation`, `GatewayTransaction`, `Refund`, `ReconciliationRecord`.

Payment providers implement an adapter contract. Callbacks are verified, idempotent, retried, and stored as raw event references for investigation.

### Customers and loyalty

Models: `Customer`, `LedgerAccount`, `LedgerEntry`, `LoyaltyAccount`, `LoyaltyTransaction`.

Support phone search, consent flags, credit limits, reminders, statements, and configurable loyalty rules.

### Reporting

Start with daily sales, payment, profit, stock, cash variance, top products, low stock, and customer-credit reports. Use pre-aggregated read models refreshed from committed events. Every report identifies shop, branch, date range, and freshness.

## 8. Industry Modules

Industry modules are isolated apps with their own models, services, permissions, API routes, reports, and sync operations.

### First module

Choose pharmacy or grocery based on the first pilot commitment:

- **Pharmacy:** batches, expiry dates, batch cost, substitutes, prescription metadata, and loose-unit conversion.
- **Grocery:** weighted items, scale configuration, barcode scanning, and khata-oriented checkout.

The shared core must remain usable without either module.

### Later modules

- Restaurant: tables, orders, kitchen tickets, modifiers, split bills, QR ordering.
- Clothing: size and color matrices, exchanges, seasonal discounts, variant stock.
- Mobile shop: IMEI units, warranty, repairs, installment plans.
- Salon or clinic: services, appointments, packages, memberships, staff commissions.

## 9. API Contract

Base path: `/api/v1/`.

- REST resources with consistent plural names and cursor pagination.
- JSON errors contain `code`, `message`, `fields`, `request_id`, and optional `details`.
- OpenAPI is generated and checked in CI for breaking changes.
- `Idempotency-Key` is required for retryable creates and mutations.
- Conditional updates use a record version or `If-Match` where edits are allowed.
- Filtering, ordering, and exposed ORM fields are allowlisted.
- Rate limits apply per IP, user, device, and shop.

Initial route groups:

```text
auth/login                 auth/refresh                 auth/devices
shops                      branches                      catalog/products
catalog/barcodes/{code}    inventory/stock               inventory/purchases
inventory/transfers        sales/carts                   sales/invoices
sales/returns              sales/shifts                 payments
customers                  customers/{id}/ledger         reports/daily
reports/profit             reports/stock-valuation       sync/pull
sync/push                  modules/{industry}/...        webhooks
```

## 10. Offline Synchronization

Offline reliability is a core capability and must be designed before finalizing the sales API.

### Client state

The client stores a local catalog, customer subset, settings, stock snapshot, invoice drafts, and an outbox. Each operation has an operation UUID, entity UUID, device ID, sequence number, creation time, payload version, and retry state.

### Push protocol

`sync/push` accepts a bounded batch. The server authenticates the device, validates the shop and branch, checks the operation UUID, validates the payload, runs the domain service in one transaction, records the result, emits changes after commit, and returns per-operation success, rejection, or conflict.

Retries return the original result. The server must never create a second invoice, payment, stock movement, or ledger entry for the same operation.

### Pull protocol

`sync/pull?cursor=<opaque>&limit=<n>` returns authorized changes. Each change includes entity type, entity ID, operation, version, timestamp, and payload or deletion marker. Cursors are durable and resumable. An expired cursor produces a full-resync response rather than silently omitting changes.

### Conflict rules

- Sales, payments, stock movements, ledgers, and audit events are append-only and accept independent device operations.
- Stock is derived from movements. Concurrent offline sales may produce negative available stock and a visible alert according to shop policy.
- Product and customer edits use version checks and an explicit last-write-wins or conflict response policy.
- Final fiscal numbers are assigned by the server when local numbering cannot satisfy regulation.
- Deletes are tombstones propagated through sync.

Test duplicate batches, retries after timeouts, out-of-order delivery, two devices selling one item, long offline periods, expired cursors, partial failures, device revocation, and schema upgrades during sync.

## 11. Background Jobs and Events

Use an outbox table so events commit with business transactions before Celery consumes them.

Jobs include WhatsApp, SMS, email and push delivery; low-stock and expiry alerts; payment reminders; owner summaries; report projection refreshes; fiscal submission retries; gateway reconciliation; subscription renewals; exports; backup verification; and cleanup.

Every task is idempotent, bounded, observable, and safe to retry. Failed tasks go to a review or dead-letter queue with tenant and request context.

## 12. Security, Privacy, and Compliance

- HTTPS, secure headers, strict CORS, CSRF protection where applicable, and secure cookies.
- Argon2 passwords, short-lived access tokens, refresh rotation, token revocation, and optional owner 2FA.
- Secrets and provider credentials are stored outside source control.
- Encrypt sensitive fields such as gateway credentials; use encrypted object storage and signed URLs.
- Audit login, permission, export, device, payment, invoice, stock, and configuration events.
- Define data export, retention, deletion, and consent workflows for the target jurisdiction.
- Run dependency, container, secret, and static security scans in CI.
- Perform tenant-isolation reviews and restore drills before production launch.

## 13. Observability and Operations

Every request and background task carries request ID, shop ID, branch ID, user ID, device ID, and correlation ID where available.

Track API latency and errors, database saturation, queue depth and retries, sync success and conflict rates, payment callback failures, reconciliation gaps, fiscal failures, report freshness, export failures, backups, and restore verification.

Production alerts need runbooks. Logs must avoid access tokens, payment secrets, and unnecessary personal data.

## 14. Environments and Delivery

Use local, test, staging, and production environments. Local development uses Docker Compose for PostgreSQL, Redis, and object storage emulation. Staging mirrors production and contains synthetic or approved test data only.

CI runs formatting, linting, type checks, migration checks, unit and integration tests, API contract tests, sync and tenant-isolation tests, dependency and secret scans, container scans, image builds, and migration safety checks.

Database changes follow expand, migrate, contract: add compatible structures, backfill safely, switch reads and writes, then remove old structures later.

## 15. Testing Strategy

- Unit tests for money, tax, discounts, stock, ledger, permissions, and conflicts.
- Integration tests for invoice, return, payment, purchase, transfer, shift, and credit workflows.
- API contract tests from OpenAPI examples.
- Tenant-isolation tests for every endpoint and asynchronous job.
- Property tests for rounding, stock conservation, ledger balance, and idempotency.
- Sync tests with multiple devices, duplicate operations, offline intervals, and network failures.
- Performance tests for checkout, barcode lookup, catalog pull, report reads, and reconnect bursts.
- Backup restore tests proving a usable environment can be recovered.

No endpoint is production-ready until authorization, tenant scope, idempotency, error behavior, and audit behavior are covered.

## 16. Delivery Roadmap

### Phase 0 — Foundation

Repository structure, Docker, CI, settings, shops, branches, users, roles, permissions, devices, tenant context, audit log, request IDs, health checks, migrations, RLS strategy, and baseline security tests.

### Phase 1 — Core POS

Catalog, barcode lookup, units, prices, tax configuration, stock movements, suppliers, purchases, invoices, returns, payments, shifts, cash drawer, customers, khata ledger, and daily reports. Implement service boundaries and immutable finalized invoices first.

### Phase 2 — Offline and Reliability

Device-scoped sync, operation idempotency, change log, cursors, outbox events, conflict responses, retries, stock alerts, and reconnect testing.

### Phase 3 — First Industry Module and Pilot

Ship pharmacy or grocery based on the first pilot commitment. Add receipts, expiry or low-stock alerts, owner summaries, local language labels, and support tools. Onboard 3–10 shops and measure checkout speed, sync success, stock accuracy, report usefulness, and support volume.

### Phase 4 — Launch Readiness

Subscription plans, entitlements, payment reconciliation, tax or fiscal integration, backups, restore drills, security review, rate-limit tuning, exports, monitoring, incident response, and rollback procedures.

### Phase 5 — Expansion

Add remaining industry modules one at a time from validated demand. Add multi-branch workflows, loyalty, webhooks, analytics, and accounting exports. Extract a component only after measured load, ownership, or isolation requirements justify it.

## 17. Success Criteria

- A new shop can be configured without engineering intervention.
- A cashier can complete sales during an outage.
- Retrying any mutation cannot duplicate financial or stock facts.
- No user or device can read or change another shop's data.
- Finalized invoices, returns, payments, stock, and credit reconcile.
- The owner can see daily sales, cash, profit estimate, low stock, and credit balances.
- Backups have been restored successfully in a drill.
- The selected industry module solves a real pilot workflow end to end.
- Monitoring, alerts, support runbooks, and rollback procedures are documented.

## 18. Risks and Architectural Decisions

- **Scope:** launch one industry module and keep the core small.
- **Sync:** settle idempotency, append-only facts, cursors, and conflict behavior before polishing checkout.
- **Tenant leakage:** combine scoped services, database policy, and adversarial tests.
- **Financial errors:** use immutable facts, explicit rounding, transactions, and reconciliation.
- **External changes:** isolate tax and payment providers behind adapters with versioned configuration.
- **Report performance:** build read models and measure before adding partitions or replicas.
- **Operations:** make every external call retryable, observable, and inspectable.

Record decisions affecting multiple modules as short ADRs in `docs/adr/`, including tenant enforcement, invoice numbering, sync conflicts, money representation, event delivery, and the first industry module.

## 19. Documentation and Testing Rules

- Product, architecture, API, operations, security, and testing documentation belongs under `docs/`.
- Every new endpoint requires API documentation with authentication, tenant headers, request examples, response examples, errors, permissions, and side effects.
- Every model requires documentation of ownership, tenant scope, lifecycle, and important invariants.
- Every architectural decision affecting more than one module requires an ADR under `docs/adr/`.
- Every feature must include unit or integration tests for its success path, authorization, tenant isolation, validation errors, idempotency where applicable, and important failure paths.
- A pull request is incomplete until its documentation and tests are updated with the implementation.
