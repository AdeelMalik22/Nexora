# Sales and Payments API

Protected sales requests require a JWT, `X-Shop-ID`, and an active shop permission. Owners bypass role permission checks.

## Checkout

1. `POST /api/v1/sales/carts/` with `{ "branch": "branch-uuid" }`.
2. `POST /api/v1/sales/carts/{id}/items/` with product or variant, quantity, unit price, and optional discount.
3. `POST /api/v1/sales/carts/{id}/finalize/` with one or more payment allocations.

Example finalization:

```json
{
  "payments": [
    {"payment_method": "payment-method-uuid", "amount": "950.0000", "reference": "optional-reference"}
  ]
}
```

Finalization is transactional. It snapshots product name, SKU, price, discount, and tax on invoice lines; records negative stock movements; creates payment records; marks the cart finalized; and emits an audit event. A payment total that does not equal the invoice total rolls back the complete transaction.

## Other endpoints

- `GET /api/v1/sales/invoices/`
- `GET|POST /api/v1/payments/methods/`
