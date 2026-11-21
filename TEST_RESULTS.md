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

## 3. Agent conversation tests

**Not run yet.** These need the API deployed over HTTPS and the published Agentplace agent. This section will be filled in with the real prompts and responses.

| # | Prompt | Expected API result | Actual API result | Agent response | Pass/Fail |
| --- | --- | --- | --- | --- | --- |
| 1 | Known product | 200 with stock | — | — | Not run |
| 2 | Unknown product | 404 `PRODUCT_NOT_FOUND` | — | — | Not run |
| 3 | Known order | 200 with status | — | — | Not run |
| 4 | Unknown order | 404 `ORDER_NOT_FOUND` | — | — | Not run |
| 5 | Malformed ID | 400 `INVALID_ID` | — | — | Not run |
| 6 | Refused request (invalid token) | 401 `UNAUTHORIZED` | — | — | Not run |
