# Accounts API

All protected endpoints require a JWT access token. Tenant-scoped endpoints also require `X-Shop-ID`.

## Signup

`POST /api/v1/auth/signup/`

```json
{
  "username": "owner",
  "email": "owner@example.com",
  "password": "a-strong-password",
  "shop_name": "My Shop",
  "branch_name": "Main Branch"
}
```

Creates the owner, shop, main branch, owner role, and membership atomically.

## Login

`POST /api/v1/auth/login/`

```json
{
  "username": "owner",
  "password": "a-strong-password",
  "shop_id": "shop-uuid",
  "device_id": "counter-tablet-01"
}
```

`shop_id` is optional for users with one active membership. `device_id` is optional until device-bound login is required. When supplied, the device must be approved and not revoked.

## Device lifecycle

- `POST /api/v1/auth/devices/` registers a device for the current shop.
- `GET /api/v1/auth/devices/list/` lists devices for authorized staff.
- `POST /api/v1/auth/devices/{id}/approve/` approves a device.
- `POST /api/v1/auth/devices/{id}/revoke/` revokes a device.

## Staff and roles

- `GET /api/v1/auth/memberships/` lists shop staff.
- `GET|POST /api/v1/auth/roles/` lists or creates roles.
- `POST /api/v1/auth/invitations/` creates a seven-day staff invitation.

Role-sensitive endpoints require the corresponding shop permission. Owners bypass role permission checks.
