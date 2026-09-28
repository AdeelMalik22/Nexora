# Inventory API

Inventory endpoints require an authenticated user with an active shop membership and `manage_inventory`, `view_inventory`, or `adjust_inventory` permission as appropriate.

```http
Authorization: Bearer <access-token>
X-Shop-ID: <shop-uuid>
X-Branch-ID: <branch-uuid>  # optional for multi-branch reads; branch is explicit in mutations
```

## Endpoints

- `GET|POST /api/v1/inventory/suppliers/`
- `GET /api/v1/inventory/stock/`
- `GET|POST /api/v1/inventory/movements/`
- `GET|POST /api/v1/inventory/purchases/`
- `POST /api/v1/inventory/purchases/receive/`
- `POST /api/v1/inventory/transfers/`
- `POST /api/v1/inventory/counts/`
- `PATCH /api/v1/inventory/stock/{balance_id}/threshold/`

Stock movements are append-only facts. Positive quantities add stock and negative quantities remove stock. The server updates a rebuildable `StockBalance` projection in the same transaction. A balance must never be edited directly to correct stock; record an adjustment movement with a reason.

Purchase receiving creates a purchase order, purchase items, purchase movements, and a received status in one transaction. Transfers create paired outbound and inbound movements. Stock counts compare counted quantities with the current projection and create adjustment movements for the difference. Low-stock thresholds are stored on each branch balance and can be updated by inventory managers.
