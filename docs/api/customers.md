# Customers and Khata API

Customer endpoints require a JWT, `X-Shop-ID`, and the corresponding customer permission.

- `GET|POST /api/v1/customers/` lists, searches, or creates customers.
- `GET /api/v1/customers/{id}/ledger/` returns the balance and append-only ledger.
- `POST /api/v1/customers/{id}/payments/` records a customer payment.

Ledger charges increase the balance; payments and refunds decrease it. Customer credit sales are linked to invoices and create a charge for the unpaid remainder during checkout. Credit limits are enforced by the ledger service. Ledger entries are never edited or deleted; corrections use a new adjustment, refund, or payment entry.
