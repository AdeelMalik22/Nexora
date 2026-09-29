# Returns and Cash API

Returns require `process_returns`; shifts require `manage_shifts`.

- `POST /api/v1/sales/returns/` restores returned quantities through append-only stock movements and creates a credit note.
- `GET|POST /api/v1/sales/shifts/` lists or opens cashier shifts.
- `POST /api/v1/sales/shifts/{id}/close/` closes a shift and records cash variance.

Returns require the original invoice, branch, reason, and invoice-item quantities. A return quantity cannot exceed the original invoice-item quantity. Optional refunds are allocated against completed payments and cannot exceed the available paid amount. All operations are transactional and audited.

Shift closing calculates expected cash from opening cash and drawer entries. The stored variance is `closing_cash - expected_cash` and requires manager review when the shop policy requires it.
