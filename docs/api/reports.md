# Reports API

Reports require a JWT, `X-Shop-ID`, and the `view_reports` permission. Owners can access reports. Date filters use `from` and `to` in ISO date format; branch filters use `branch` UUID.

- `GET /api/v1/reports/daily/` — invoice count, sales, tax, discounts, and payments.
- `GET /api/v1/reports/profit/` — sales and estimated profit. Cost is explicitly marked unavailable until cost layers are introduced.
- `GET /api/v1/reports/stock-valuation/` — branch stock balances and low-stock flags.
- `GET /api/v1/reports/credit/` — customer balances and credit limits.
- `GET /api/v1/reports/cash/` — shifts, closing cash, and cash variance.

Report responses identify their date and branch scope through the request filters. Read models and scheduled aggregation can replace direct queries as data volume grows without changing the API contract.
