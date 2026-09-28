# Tenant API Rules

Every protected tenant request must include:

```http
Authorization: Bearer <access-token>
X-Shop-ID: <shop-uuid>
X-Branch-ID: <branch-uuid>  # required for branch-scoped operations
```

The server validates that the authenticated user has an active membership in the selected shop. Tenant query managers return no rows without an active context, and PostgreSQL RLS applies the same shop boundary at the database layer.

Clients must treat shop IDs as opaque identifiers and must never select a shop by trusting a value from an unverified token or URL alone.

When `X-Branch-ID` is supplied, the branch must belong to the selected shop and be active. The selected branch is available to application services through the request and tenant context helpers.
