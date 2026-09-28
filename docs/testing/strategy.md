# Testing Strategy

Every feature must cover the normal workflow and the boundaries around it.

## Required layers

- Unit tests for pure business rules and policy decisions.
- Integration tests for transactions, models, migrations, and external adapters.
- API tests for authentication, permissions, validation, response contracts, and side effects.
- Tenant isolation tests for every tenant-scoped endpoint and asynchronous operation.
- Regression tests for every fixed defect.

## Minimum feature coverage

Each feature should test:

1. successful behavior;
2. unauthenticated and unauthorized access;
3. access from a different shop;
4. invalid input and missing context;
5. duplicate or retry behavior where mutations are involved;
6. audit events and important state transitions.

## Running tests

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py test
```

Tests must be deterministic, use isolated databases, and must not require production credentials or external services.
