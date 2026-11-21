# Agentplace Backend Engineer Assessment — Project Specification

## 1. Purpose

Build a small, reliable store API and connect an Agentplace store agent to it.

This project is specifically scoped to the official Agentplace Backend Engineer assessment. The assessment requires:

1. A service containing 10 sample products and 10 sample orders.
2. Two read operations: product stock level and order status.
3. Parameter validation and authorization.
4. An Agentplace store agent built with the free Luna model that checks stock and order status through the API.
5. Tests for existing records, unknown records, an invalid ID, and a request the API refuses.
6. A record of the tests and how the agent responded.
7. An email to `nikita@agentplace.io` with subject `Application: Backend Engineer`, including the published agent link and repository with code, setup instructions, and test results.

Official specification: https://agentplace.io/careers/backend-engineer

## 2. Technology decisions

- Python
- Django
- Django REST Framework
- SQLite 3
- Gunicorn
- Caddy for HTTPS and reverse proxy
- Ubuntu VPS
- GitHub
- Agentplace with the free Luna model

### Why SQLite

SQLite is sufficient for this small assessment service. The dataset is tiny and the API is primarily read-only. It avoids adding a database server that the task does not require.

Deployment requirements:
- Keep the SQLite database on persistent server storage, outside the Git repository.
- Do not commit the database file or secrets.
- Ensure the Gunicorn service user can write to the database directory.
- Back up the database file.
- Use a single application instance initially; SQLite is not intended here for high-concurrency write workloads.

### Reverse proxy

Caddy will terminate HTTPS and proxy requests to Gunicorn over localhost. Nginx is not required in this setup.

## 3. Deliberately limited scope

Build only what the assessment needs.

Included:
- Product, Order, and OrderItem models.
- Exactly 10 seeded products and 10 seeded orders.
- Two authenticated GET endpoints.
- Input validation.
- Consistent JSON success and error responses.
- Automated API tests.
- A small seed-data command or fixture.
- Deployment configuration/instructions for Gunicorn and Caddy.
- Agentplace configuration instructions and test report.

Not included unless the assessment reveals a real need:
- React or another frontend.
- Celery or Redis.
- PostgreSQL.
- Docker.
- Nginx.
- Payment processing.
- Order creation, cancellation, or modification endpoints.
- Admin dashboards or unrelated CRUD endpoints.
- Complex role/permission systems.
- Unnecessary abstraction layers or generic repository/service patterns.

## 4. Data model

### Product

- `id`: UUID primary key
- `sku`: unique string
- `name`: string
- `description`: optional text
- `stock_quantity`: non-negative integer
- `is_active`: boolean

### Order

- `id`: UUID primary key
- `order_number`: unique string
- `customer_name`: string
- `status`: controlled choice
- `created_at`: timestamp

Suggested order statuses:
- `pending`
- `confirmed`
- `processing`
- `shipped`
- `delivered`
- `cancelled`

### OrderItem

- `id`: UUID primary key
- `order`: foreign key to Order
- `product`: foreign key to Product
- `quantity`: positive integer
- `unit_price`: decimal

The order-item relationship makes the sample orders realistic while keeping the required API read-only.

## 5. API contract

Base path: `/api/`

Both endpoints require an API credential in the HTTP `Authorization` header.

### 5.1 Check product stock

`GET /api/products/{product_id}/stock/`

- `product_id` must be a valid UUID.
- Return the product's ID, SKU, name, stock quantity, and whether it is in stock.
- Do not return inactive products as available stock.

Example success:

```json
{
  "success": true,
  "data": {
    "product_id": "UUID",
    "sku": "SKU-1001",
    "name": "Wireless Mouse",
    "stock_quantity": 25,
    "in_stock": true
  }
}
```

### 5.2 Check order status

`GET /api/orders/{order_id}/status/`

- `order_id` must be a valid UUID.
- Return the order number, current status, and creation timestamp.
- Do not expose unnecessary customer personal information.

Example success:

```json
{
  "success": true,
  "data": {
    "order_id": "UUID",
    "order_number": "ORD-1001",
    "status": "shipped",
    "created_at": "2026-11-21T10:00:00Z"
  }
}
```

## 6. Authentication and authorization

Use one dedicated API token for the Agentplace integration.

- Store the expected token in an environment variable, never in source code.
- Require `Authorization: Bearer <token>`.
- Reject missing, malformed, or incorrect credentials.
- Use constant-time token comparison.
- Never log the token.
- Do not put the token in a URL or query parameter.
- Configure the token as a secret in the Agentplace API/action connection, not in public agent instructions.

Expected unauthorized response:

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Valid API credentials are required."
  }
}
```

## 7. Error contract

Use predictable HTTP status codes and stable machine-readable error codes.

| Situation | HTTP | Error code |
|---|---:|---|
| Missing or invalid token | 401 | `UNAUTHORIZED` |
| Malformed UUID | 400 | `INVALID_ID` |
| Valid UUID, product does not exist | 404 | `PRODUCT_NOT_FOUND` |
| Valid UUID, order does not exist | 404 | `ORDER_NOT_FOUND` |
| Unsupported HTTP method | 405 | `METHOD_NOT_ALLOWED` |

Example not-found response:

```json
{
  "success": false,
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product was not found."
  }
}
```

Do not return stack traces, database details, environment variables, or secrets to API clients.

## 8. Required test matrix

The repository must include automated tests for at least these cases:

| Test | Request | Expected result |
|---|---|---|
| Existing product | Valid token + existing product UUID | 200 with stock data |
| Unknown product | Valid token + valid but unknown UUID | 404 `PRODUCT_NOT_FOUND` |
| Existing order | Valid token + existing order UUID | 200 with order status |
| Unknown order | Valid token + valid but unknown UUID | 404 `ORDER_NOT_FOUND` |
| Invalid ID | Valid token + malformed UUID | 400 `INVALID_ID` |
| Refused request | Missing or wrong token | 401 `UNAUTHORIZED` |
| Wrong method | POST to a read-only endpoint | 405 |

The test report must record actual observed results. Never mark a test as passed unless it was run.

## 9. Agentplace configuration

Create an Agentplace account and build a store-support agent using the free Luna model.

The agent needs two API-backed capabilities:

### Capability A: `check_product_stock`

Inputs:
- `product_id` (string UUID)

Action:
- Send an authenticated GET request to `/api/products/{product_id}/stock/`.

### Capability B: `check_order_status`

Inputs:
- `order_id` (string UUID)

Action:
- Send an authenticated GET request to `/api/orders/{order_id}/status/`.

Configure the Bearer token as a secret/credential in the platform's supported connection settings. Do not expose it in user-visible prompts, conversation text, screenshots, or a public repository.

Agent behavior:
- Ask for the required identifier if the customer has not provided it.
- Call the relevant API operation instead of guessing.
- Base stock and order answers only on API results.
- Explain a not-found result plainly without inventing data.
- If authorization or the API is unavailable, say it cannot retrieve the information and do not fabricate an answer.
- Do not disclose credentials or internal error details.

The exact Agentplace UI labels and connection mechanism must be confirmed in the live workspace; do not assume a feature name before inspecting the builder.

## 10. Agent conversation test matrix

After connecting the API, test these through the published agent:

1. Ask about a known product and verify the returned stock quantity.
2. Ask about an unknown product and verify the agent explains it was not found.
3. Ask about a known order and verify the returned order status.
4. Ask about an unknown order and verify the agent does not invent a status.
5. Provide a malformed identifier and verify validation is handled clearly.
6. Test a refused API request (for example, by temporarily using an invalid credential in a safe test configuration) and verify the agent does not claim success.

Record:
- User prompt
- Expected API behavior
- Actual API response/status
- Agent response
- Pass/fail
- Notes or screenshot reference

## 11. Deployment outline

### Application process

Gunicorn listens only on localhost, for example `127.0.0.1:8000`.

Caddy:
- Owns the public hostname.
- Obtains and renews the TLS certificate.
- Redirects HTTP to HTTPS.
- Reverse-proxies HTTPS requests to Gunicorn.

Do not expose Gunicorn directly to the public internet.

### Server configuration

- Set `DEBUG=False`.
- Set `ALLOWED_HOSTS` to the API hostname.
- Set a strong Django `SECRET_KEY` in the environment.
- Set the API token in the environment.
- Set `CSRF_TRUSTED_ORIGINS` only if needed by the selected deployment.
- Configure secure proxy/HTTPS settings correctly for Caddy.
- Run migrations before starting the service.
- Keep `db.sqlite3` in persistent storage and out of Git.
- Run Gunicorn under a dedicated non-root system user.
- Use a systemd service with restart behavior.
- Restrict firewall access to SSH and public HTTP/HTTPS as appropriate.
- Keep secrets in server environment/config files with restrictive permissions.

### Example Caddy routing concept

```caddyfile
api.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

Replace `api.example.com` with the real hostname. DNS must point to the VPS and ports 80/443 must be reachable for automatic HTTPS.

## 12. Minimal repository layout

```text
agentplace-store-api/
├── config/
├── store/
│   └── tests/
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── TEST_RESULTS.md
```

Only add files that are needed. Do not commit:
- `.env`
- API tokens
- Django secret keys
- `db.sqlite3`
- virtual environments
- Python cache files
- local logs

## 13. README requirements

The repository README must explain:
- Project purpose.
- Python version.
- Local setup.
- Environment variables.
- Database migration and seed-data commands.
- How to run the development server.
- How to run tests.
- API endpoints and example requests.
- Authentication format.
- Deployment overview.
- Agentplace setup at a high level.

## 14. Final submission

Email: `nikita@agentplace.io`

Subject: `Application: Backend Engineer`

Include:
1. Published Agentplace agent URL.
2. GitHub repository URL.
3. Setup instructions in the repository.
4. Actual automated API test results.
5. Agent conversation test results.

Do not submit until the API is reachable over HTTPS, the agent can successfully call both operations, and the test report reflects real test runs.

## 15. Working rules

- Implement the smallest solution that completely satisfies the assessment.
- Prefer clear, conventional Django/DRF code over clever abstractions.
- Never hardcode secrets.
- Never invent test results.
- Keep the API read-only.
- Do not add technologies or features without a concrete requirement.
- Verify the current Agentplace builder interface before writing platform-specific setup instructions.
