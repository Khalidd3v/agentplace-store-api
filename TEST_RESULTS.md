# Test Results

This file records only tests that have actually been run.

## 1. Automated API tests

- **Command:** `python manage.py test`
- **Run:** 2026-11-21 07:36 UTC, on a local machine
- **Versions:** Python 3.13.7, Django 5.2.19, Django REST Framework 3.18.3, Simple JWT 5.5.1
- **Result:** `Ran 18 tests in 0.043s` `OK`

| Case | Test | Expected | Result |
| --- | --- | --- | --- |
| Existing product | `test_existing_product_returns_stock` | 200 with stock data | Pass |
| Unknown product | `test_unknown_product_returns_404` | 404 `PRODUCT_NOT_FOUND` | Pass |
| Existing order | `test_existing_order_returns_status` | 200 with order status | Pass |
| Unknown order | `test_unknown_order_returns_404` | 404 `ORDER_NOT_FOUND` | Pass |
| Invalid product ID | `test_invalid_product_id_returns_400` | 400 `INVALID_ID` | Pass |
| Invalid order ID | `test_invalid_order_id_returns_400` | 400 `INVALID_ID` | Pass |
| Missing token | `test_missing_token_is_refused` | 401 `UNAUTHORIZED` | Pass |
| Wrong token | `test_wrong_token_is_refused` | 401 `UNAUTHORIZED` | Pass |
| Malformed `Authorization` header | `test_malformed_header_is_refused` | 401 `UNAUTHORIZED` | Pass |
| Token in query string | `test_token_in_query_string_is_refused` | 401 `UNAUTHORIZED` | Pass |
| Expired token | `test_expired_token_is_refused` | 401 `UNAUTHORIZED` | Pass |
| Token of an inactive user | `test_inactive_user_is_refused` | 401 `UNAUTHORIZED` | Pass |
| POST to a read-only endpoint | `test_post_is_not_allowed` | 405 `METHOD_NOT_ALLOWED` | Pass |
| Product with zero stock | `test_product_with_zero_stock_is_not_in_stock` | `in_stock: false` | Pass |
| Inactive product | `test_inactive_product_is_not_reported_as_available` | `stock_quantity: 0`, `in_stock: false` | Pass |
| No customer details in order response | `test_order_response_has_no_customer_details` | Customer name absent | Pass |
| Seed command run twice | `test_seed_is_idempotent` | Exactly 10 products and 10 orders | Pass |
| Agent token command | `test_create_agent_token_returns_working_30_day_token` | 30-day JWT that authenticates | Pass |

## 2. Manual smoke test against Gunicorn

- **Run:** 2026-11-21, on a local machine
- **Setup:** `migrate`, `seed_store`, and `create_agent_token`, then Gunicorn on `127.0.0.1` with 2 workers. Requests were sent with `curl`.

| Request | HTTP | Response |
| --- | ---: | --- |
| Product `…0001` | 200 | `{"success":true,"data":{"product_id":"a1000000-0000-4000-8000-000000000001","sku":"SKU-1001","name":"Wireless Mouse","stock_quantity":25,"in_stock":true}}` |
| Product `…0009` (inactive) | 200 | `{"success":true,"data":{…,"sku":"SKU-1009","name":"LED Desk Lamp","stock_quantity":0,"in_stock":false}}` |
| Unknown product | 404 | `{"success":false,"error":{"code":"PRODUCT_NOT_FOUND","message":"Product was not found."}}` |
| Order `…0002` | 200 | `{"success":true,"data":{"order_id":"b2000000-0000-4000-8000-000000000002","order_number":"ORD-1002","status":"shipped","created_at":"2026-11-10T14:30:00Z"}}` |
| Unknown order | 404 | `{"success":false,"error":{"code":"ORDER_NOT_FOUND","message":"Order was not found."}}` |
| Order ID `abc` | 400 | `{"success":false,"error":{"code":"INVALID_ID","message":"The ID must be a valid UUID."}}` |
| No token | 401 | `{"success":false,"error":{"code":"UNAUTHORIZED","message":"Valid API credentials are required."}}` |
| Wrong token | 401 | `{"success":false,"error":{"code":"UNAUTHORIZED","message":"Valid API credentials are required."}}` |
| POST with a valid token | 405 | `{"success":false,"error":{"code":"METHOD_NOT_ALLOWED","message":"This endpoint only supports GET."}}` |

## 3. Live API checks over HTTPS

- **Run:** 2026-11-21, against the production deployment (Caddy with a Let's Encrypt certificate, Gunicorn, SQLite)
- **Client:** `curl` from an external machine, using a JWT created by `create_agent_token`

| Check | Result |
| --- | --- |
| HTTP request | 308 redirect to HTTPS |
| Known product (`…0001`, `…0003`, `…0009`) | 200 with stock 25 / 0 / 0. `in_stock` is true / false / false |
| All 10 seeded orders | 200 with the expected status for each |
| Unknown product / unknown order | 404 `PRODUCT_NOT_FOUND` / 404 `ORDER_NOT_FOUND` |
| Invalid ID (`abc`) | 400 `INVALID_ID` |
| No token / wrong token | 401 `UNAUTHORIZED` |
| POST with a valid token | 405 `METHOD_NOT_ALLOWED` |
| Unknown URL | Plain 404 page, with no debug output |
| Gunicorn port 8000 from outside | Not reachable |

Server processing time was 0.2–1.2 s per request. Some requests from the test machine took longer to connect, because of packet loss on that network path (50% ICMP loss). Measured connect and TLS times show the delay was before the request reached the server.

## 4. Agent tests

- **Agent:** https://ldhrw5ouiy4r.run.agentplace.io (Agentplace, Luna model)
- **Run:** 2026-11-21, with the Agentplace builder against the live API
- **Actions:** `check_product_stock` and `check_order_status`, both authenticated with a Bearer token stored as a secret. The builder reported that all 7 action tests passed, with 0 build errors and 0 warnings.

| # | Input | Expected API result | Agent result | Pass/Fail |
| --- | --- | --- | --- | --- |
| 1 | Product `a1000000-0000-4000-8000-000000000001` | 200, stock 25 | "Wireless Mouse (SKU-1001): 25 in stock." | Pass |
| 1b | Product `a1000000-0000-4000-8000-000000000003` | 200, stock 0 | "USB-C Hub (SKU-1003): 0, out of stock." | Pass |
| 1c | Product `a1000000-0000-4000-8000-000000000009` (inactive) | 200, stock 0, `in_stock: false` | "LED Desk Lamp (SKU-1009): 0, not in stock." | Pass |
| 2 | Product `00000000-0000-4000-8000-000000000000` | 404 `PRODUCT_NOT_FOUND` | "Not found." | Pass |
| 3 | Order `b2000000-0000-4000-8000-000000000002` | 200, `shipped` | "ORD-1002: shipped." | Pass |
| 3b | Order `b2000000-0000-4000-8000-000000000006` | 200, `cancelled` | "ORD-1006: cancelled." | Pass |
| 4 | Order `00000000-0000-4000-8000-000000000000` | 404 `ORDER_NOT_FOUND` | "Not found." No status was made up. | Pass |
| 5 | Product and order ID `12345` | 400 `INVALID_ID` | "Invalid ID." | Pass |
| 6 | Request refused because of an invalid token | 401 `UNAUTHORIZED` | — | Not run |

Notes:

- During setup, the builder first tested with made-up IDs that were not UUIDs. The API rejected them with 400 `INVALID_ID`, which confirmed that validation works at the live endpoint. The builder then mapped 400 to "invalid ID" and 404 to "not found".
- The agent does not list products, because the API has no list endpoint. It asks the customer for a product ID instead.
