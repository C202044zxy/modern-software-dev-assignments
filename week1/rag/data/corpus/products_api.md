# Products API

Base URL: https://api.acme.example/v1

## GET /products
Returns a paginated list of products. Supports query parameters `limit` (default
20, max 100) and `cursor` for pagination. Response body:
`{"items": [...], "next_cursor": "<string|null>"}`.

## GET /products/{sku}
Returns the product with the given SKU. Response includes `sku`, `name`,
`price_cents`, `currency`, and `in_stock` (boolean).

## POST /products
Creates a new product. Required fields: `sku`, `name`, `price_cents`,
`currency`. The `sku` must be unique; submitting a duplicate SKU returns 409.

Prices are always represented as integer cents in the smallest unit of the
currency. For example, USD $19.99 is `1999`, and JPY 500 is `500`.
