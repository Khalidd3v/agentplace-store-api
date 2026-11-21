# Test Results

This file records real test runs only. A test is marked as passed only after it has actually been run.

## 1. Automated API tests

- **Command:** `python manage.py test -v 2`
- **Run at:** 2026-11-21 07:23 UTC, on a local machine (macOS)
- **Environment:** Python 3.13.7, Django 5.2.19, Django REST Framework 3.18.3
- **Result:** 19 tests ran, 19 passed (`OK`)

Assessment matrix:

| Case | Request | Expected | Test | Result |
| --- | --- | --- | --- | --- |
| Existing product | Valid token + existing product UUID | 200 with stock data | `test_existing_product_returns_stock` | Pass |
| Unknown product | Valid token + unknown UUID | 404 `PRODUCT_NOT_FOUND` | `test_unknown_product_returns_404` | Pass |
| Existing order | Valid token + existing order UUID | 200 with order status | `test_existing_order_returns_status` | Pass |
| Unknown order | Valid token + unknown UUID | 404 `ORDER_NOT_FOUND` | `test_unknown_order_returns_404` | Pass |
| Invalid ID | Valid token + malformed UUID | 400 `INVALID_ID` | `ProductStockTests` / `OrderStatusTests.test_malformed_id_returns_400` | Pass |
| Refused request | Missing token | 401 `UNAUTHORIZED` | `test_missing_token_is_refused` | Pass |
| Refused request | Wrong token | 401 `UNAUTHORIZED` | `test_wrong_token_is_refused` | Pass |
| Wrong method | `POST` with a valid token | 405 `METHOD_NOT_ALLOWED` | `test_post_is_not_allowed` | Pass |

Additional tests:

| Test | Checks | Result |
| --- | --- | --- |
| `test_product_with_zero_stock_is_not_in_stock` | Zero stock gives `in_stock: false` | Pass |
| `test_inactive_product_is_not_reported_as_available` | An inactive product reports `0` and `in_stock: false` | Pass |
| `test_order_response_excludes_customer_details` | The customer name is not in the response | Pass |
| `test_malformed_header_is_refused` | A bare token, `Token x`, `Bearer` alone, and extra parts are all refused with 401 | Pass |
| `test_token_in_query_string_is_refused` | `?token=` is not accepted | Pass |
| `test_auth_is_checked_before_id_validation` | An unauthenticated request with a bad ID gets 401, not 400 | Pass |
| `test_unconfigured_token_refuses_everything` | An empty `STORE_API_TOKEN` refuses every request | Pass |
| `test_post_without_token_is_refused` | `POST` without a token gets 401 | Pass |
| `test_unknown_route_returns_json_404` | An unknown URL gets a JSON 404 `NOT_FOUND` | Pass |
| `test_seed_creates_ten_products_and_orders_idempotently` | Running the seed twice leaves exactly 10 products and 10 orders, all with items | Pass |

Output (abridged):

```text
Ran 19 tests in 0.029s

OK
```

## 2. Manual smoke test against Gunicorn

- **Run at:** 2026-11-21, locally
- **Setup:** `migrate`, then `seed_store`, then Gunicorn on `127.0.0.1` with 2 workers. Requests were made with `curl`.

| Request | HTTP | Response body |
| --- | ---: | --- |
| GET product `…0001` (Wireless Mouse) | 200 | `{"success":true,"data":{"product_id":"a1000000-0000-4000-8000-000000000001","sku":"SKU-1001","name":"Wireless Mouse","stock_quantity":25,"in_stock":true}}` |
| GET product `…0009` (inactive) | 200 | `{"success":true,"data":{…,"sku":"SKU-1009","name":"LED Desk Lamp","stock_quantity":0,"in_stock":false}}` |
| GET unknown product | 404 | `{"success":false,"error":{"code":"PRODUCT_NOT_FOUND","message":"Product was not found."}}` |
| GET order `…0002` | 200 | `{"success":true,"data":{"order_id":"b2000000-0000-4000-8000-000000000002","order_number":"ORD-1002","status":"shipped","created_at":"2026-11-10T14:30:00Z"}}` |
| GET unknown order | 404 | `{"success":false,"error":{"code":"ORDER_NOT_FOUND","message":"Order was not found."}}` |
| GET order `abc` | 400 | `{"success":false,"error":{"code":"INVALID_ID","message":"The ID must be a valid UUID."}}` |
| GET order, no token | 401 | `{"success":false,"error":{"code":"UNAUTHORIZED","message":"Valid API credentials are required."}}` |
| GET order, wrong token | 401 | `{"success":false,"error":{"code":"UNAUTHORIZED","message":"Valid API credentials are required."}}` |
| POST order, valid token | 405 | `{"success":false,"error":{"code":"METHOD_NOT_ALLOWED","message":"This endpoint only supports GET."}}` |

`python manage.py check --deploy` with `DJANGO_DEBUG=False` reported no issues. Four checks are intentionally silenced, with reasons given in `config/settings.py`.

## 3. Agent conversation tests

**Status: not run yet.** These need the API deployed over HTTPS and the published Agentplace agent connected to it. This section will be filled in with the real prompts and responses.

| # | User prompt | Expected API behaviour | Actual API response | Agent response | Pass/Fail | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Known product | 200, stock quantity | — | — | Not run | |
| 2 | Unknown product | 404 `PRODUCT_NOT_FOUND` | — | — | Not run | |
| 3 | Known order | 200, order status | — | — | Not run | |
| 4 | Unknown order | 404 `ORDER_NOT_FOUND` | — | — | Not run | |
| 5 | Malformed ID | 400 `INVALID_ID` | — | — | Not run | |
| 6 | Refused request (invalid token in a test setup) | 401 `UNAUTHORIZED` | — | — | Not run | |
