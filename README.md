# Nexora

Nexora is a multi-tenant, offline-capable point-of-sale platform for small and medium businesses. It provides a shared POS core with industry modules for pharmacy, grocery, restaurant, clothing, mobile shops, and salons or clinics.

The platform is designed around reliable sales, inventory, payments, customer credit, auditability, tenant isolation, and safe synchronization after offline use.

## Current status

The project is in Phase 0 foundation development.

Implemented so far:

- Django modular monolith structure
- Local, test, and production settings
- PostgreSQL and Redis development services
- Shop, branch, and enabled-module models
- UUID and timestamp model primitives
- Custom UUID-based user model
- Shop memberships, roles, and permissions
- JWT login and refresh-token rotation
- Device registration, approval, listing, and revocation
- Device credentials and branch-aware tenant context
- Staff invitation acceptance and membership activation controls
- Tenant-aware request context and scoped query helpers
- PostgreSQL Row-Level Security setup
- Audit log model and event service
- Audit log API, Celery configuration, production container, and CI checks
- Catalog products, variants, units, categories, barcodes, tax categories, and price lists
- Inventory suppliers, append-only movements, and branch stock balances
- Sales carts, immutable invoice snapshots, stock deduction, and payments
- Customer profiles, credit limits, and append-only khata ledger
- Daily sales, stock, credit, cash, and profit reports
- Health endpoints
- Documentation and tenant-isolation test foundations

## Product capabilities planned

- Catalog and barcode-based checkout
- Inventory movements, purchases, transfers, and stock audits
- Invoices, returns, shifts, and cash drawers
- Split payments and local payment gateway adapters
- Customer credit ledger, loyalty, and reminders
- Offline push and pull synchronization
- Daily sales, profit, stock, and cash reports
- WhatsApp, SMS, email, and push notifications
- Tax and fiscal invoice integrations
- Industry-specific workflows enabled per shop

## Technology

- Python and Django
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- JWT authentication
- Docker Compose for local infrastructure
- S3-compatible object storage for files and exports

## Repository structure

```text
config/          Django settings, URLs, ASGI, WSGI, and Celery configuration
apps/            Bounded-context applications
  accounts/      Users, roles, memberships, devices, authentication
  audit/         Audit events
  common/        Shared primitives, health checks, and tenant context
  tenants/       Shops, branches, and module enablement
  industry/      Pharmacy, grocery, restaurant, and other modules
tests/           Cross-module test suites
docs/            API, architecture, development, operations, security, and testing docs
docker/          Container and deployment assets
manage.py        Django management entry point
```

## Local setup

### 1. Create or activate the environment

The project uses a local virtual environment at `.venv/`.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

For local SQLite development, the default settings are sufficient. PostgreSQL settings are provided for Docker or a local PostgreSQL instance.

### 3. Start infrastructure services

```bash
docker compose up -d postgres redis
```

### 4. Run migrations and checks

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py check
```

### 5. Start the development server

```bash
.venv/bin/python manage.py runserver
```

Health endpoints:

```text
GET /health/live/
GET /health/ready/
```

## Authentication and tenant requests

Login and refresh endpoints:

```text
POST /api/v1/auth/signup/
POST /api/v1/auth/login/
POST /api/v1/auth/refresh/
```

Tenant-scoped requests require both headers:

```http
Authorization: Bearer <access-token>
X-Shop-ID: <shop-uuid>
```

The server validates shop membership before setting tenant context. Queries without a tenant context fail closed. PostgreSQL RLS provides a second database-level boundary.

## Testing

Run the full test suite with:

```bash
.venv/bin/python manage.py test
```

Run the current accounts and tenant tests with:

```bash
.venv/bin/python manage.py test apps.accounts.tests
```

Features should include tests for success, validation, authentication, authorization, tenant isolation, retries, and important state transitions.

## Documentation

Documentation is part of the definition of done. Start with the [documentation index](docs/README.md).

- [API documentation](docs/api/README.md)
- [Accounts API](docs/api/accounts.md)
- [Tenant API rules](docs/api/tenants.md)
- [Catalog API](docs/api/catalog.md)
- [Inventory API](docs/api/inventory.md)
- [Sales and payments API](docs/api/sales.md)
- [Customers and khata API](docs/api/customers.md)
- [Reports API](docs/api/reports.md)
- [Documentation rules](docs/development/documentation.md)
- [Testing strategy](docs/testing/strategy.md)
- [Backend plan](plan.md)

Architecture decisions belong in `docs/adr/`. Endpoint and model changes must update the relevant documentation in the same pull request.

## Development workflow

1. Create a focused feature branch from the latest `master`.
2. Implement the feature within its owning app and public service boundaries.
3. Add migrations, tests, and documentation in the same change.
4. Run checks and the relevant test suite locally.
5. Push the branch and open a pull request into `master`.

`master` is kept stable; larger foundation work may remain together in a feature branch until its planned phase slice is complete.

## License

License terms have not been selected yet.
