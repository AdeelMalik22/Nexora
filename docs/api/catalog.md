# Catalog API

Catalog endpoints require a JWT and an active shop membership:

```http
Authorization: Bearer <access-token>
X-Shop-ID: <shop-uuid>
```

The caller must have the `manage_catalog` permission unless they are a shop owner.

## Resources

- `GET|POST /api/v1/catalog/categories/`
- `GET|POST /api/v1/catalog/units/`
- `GET|POST /api/v1/catalog/tax-categories/`
- `GET|POST /api/v1/catalog/products/`
- `GET|POST /api/v1/catalog/variants/`
- `GET|POST /api/v1/catalog/barcodes/`
- `GET|POST /api/v1/catalog/price-lists/`
- `GET|POST /api/v1/catalog/prices/`

Product search uses `GET /api/v1/catalog/products/?search=rice`. Barcode lookup uses `GET /api/v1/catalog/barcodes/?code=8900001`.

Products, categories, units, prices, and barcodes are shop-scoped. Prices include validity timestamps so later sales can snapshot the exact amount used at checkout. A barcode must target a product or variant, and a price must target a product or variant.
