# Agentplace Store API

A small, read-only store API used by an [Agentplace](https://agentplace.io) store-support agent. The agent runs on the free Luna model and looks up product stock and order status by calling this API.

It was built for the [Agentplace Backend Engineer assessment](https://agentplace.io/careers/backend-engineer).

- 10 sample products and 10 sample orders, with order items
- Two authenticated `GET` endpoints: product stock and order status
- UUID validation, bearer-token authorization, and consistent JSON errors
- Automated tests for every case in the assessment

**Stack:** Python 3.13, Django 5.2, Django REST Framework, SQLite, Gunicorn, Caddy.

## Contents

- [Local setup](#local-setup)
- [Environment variables](#environment-variables)
- [API](#api)
- [Tests](#tests)
- [Deployment](#deployment)
- [Agentplace setup](#agentplace-setup)
- [Project layout](#project-layout)

## Local setup

Requires Python 3.13.

```bash
git clone https://github.com/Khalidd3v/agentplace-store-api.git
cd agentplace-store-api

python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: set DJANGO_SECRET_KEY and STORE_API_TOKEN (generation commands are in the file).

python manage.py migrate
python manage.py seed_store
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/api/`.

`seed_store` is idempotent. Running it again resets the 10 products and 10 orders to their sample values without creating duplicates.

## Environment variables

Settings are read from the environment. For local development, the app also loads a `.env` file in the project root.

| Variable | Required | Description |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Yes | Django secret key. The app will not start without it. |
| `STORE_API_TOKEN` | Yes | The bearer token API clients must send. If it is empty, every request is refused. |
| `DJANGO_DEBUG` | No | `True` for local development. Defaults to `False`. |
| `DJANGO_ALLOWED_HOSTS` | In production | Comma-separated hostnames, for example `api.example.com`. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | No | Comma-separated origins. This API does not need it. |
| `SQLITE_PATH` | No | Path of the SQLite database. Defaults to `./db.sqlite3`. |

Never commit `.env`, tokens, secret keys, or the database file. `.gitignore` already excludes them.

## API

Base path: `/api/`. Every request must include this header:

```
Authorization: Bearer <STORE_API_TOKEN>
```

The token is compared in constant time. It is only accepted in the header, never in the URL or query string.

### Check product stock

`GET /api/products/{product_id}/stock/`

```bash
curl -H "Authorization: Bearer $STORE_API_TOKEN" \
  http://127.0.0.1:8000/api/products/a1000000-0000-4000-8000-000000000001/stock/
```

```json
{
  "success": true,
  "data": {
    "product_id": "a1000000-0000-4000-8000-000000000001",
    "sku": "SKU-1001",
    "name": "Wireless Mouse",
    "stock_quantity": 25,
    "in_stock": true
  }
}
```

`stock_quantity` is the stock that can be sold. Inactive (discontinued) products always report `0` and `"in_stock": false`.

### Check order status

`GET /api/orders/{order_id}/status/`

```bash
curl -H "Authorization: Bearer $STORE_API_TOKEN" \
  http://127.0.0.1:8000/api/orders/b2000000-0000-4000-8000-000000000002/status/
```

```json
{
  "success": true,
  "data": {
    "order_id": "b2000000-0000-4000-8000-000000000002",
    "order_number": "ORD-1002",
    "status": "shipped",
    "created_at": "2026-11-10T14:30:00Z"
  }
}
```

The response does not include customer details. Possible statuses are `pending`, `confirmed`, `processing`, `shipped`, `delivered`, and `cancelled`.

### Errors

Every error has the same shape:

```json
{
  "success": false,
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product was not found."
  }
}
```

| Situation | HTTP | `error.code` |
| --- | ---: | --- |
| Missing, malformed, or wrong token | 401 | `UNAUTHORIZED` |
| ID is not a valid UUID | 400 | `INVALID_ID` |
| Valid UUID, but no such product | 404 | `PRODUCT_NOT_FOUND` |
| Valid UUID, but no such order | 404 | `ORDER_NOT_FOUND` |
| Method other than `GET` | 405 | `METHOD_NOT_ALLOWED` |
| Unknown URL | 404 | `NOT_FOUND` |
| Unexpected server error | 500 | `SERVER_ERROR` |

Authorization is checked first. An unauthenticated request gets a 401 whatever else is wrong with it. Error responses never include stack traces, database details, or configuration.

### Sample data

The seeded records have fixed IDs, so you can use them in tests and agent conversations.

| Product ID | SKU | Name | Stock | Notes |
| --- | --- | --- | ---: | --- |
| `a1000000-0000-4000-8000-000000000001` | SKU-1001 | Wireless Mouse | 25 | |
| `a1000000-0000-4000-8000-000000000002` | SKU-1002 | Mechanical Keyboard | 12 | |
| `a1000000-0000-4000-8000-000000000003` | SKU-1003 | USB-C Hub | 0 | Out of stock |
| `a1000000-0000-4000-8000-000000000004` | SKU-1004 | 27-inch Monitor | 7 | |
| `a1000000-0000-4000-8000-000000000005` | SKU-1005 | Laptop Stand | 40 | |
| `a1000000-0000-4000-8000-000000000006` | SKU-1006 | HD Webcam | 15 | |
| `a1000000-0000-4000-8000-000000000007` | SKU-1007 | Noise-Cancelling Headphones | 3 | |
| `a1000000-0000-4000-8000-000000000008` | SKU-1008 | 1TB External SSD | 18 | |
| `a1000000-0000-4000-8000-000000000009` | SKU-1009 | LED Desk Lamp | 9 | Inactive, reported as 0 |
| `a1000000-0000-4000-8000-000000000010` | SKU-1010 | HDMI Cable 2m | 60 | |

| Order ID | Number | Status |
| --- | --- | --- |
| `b2000000-0000-4000-8000-000000000001` | ORD-1001 | delivered |
| `b2000000-0000-4000-8000-000000000002` | ORD-1002 | shipped |
| `b2000000-0000-4000-8000-000000000003` | ORD-1003 | processing |
| `b2000000-0000-4000-8000-000000000004` | ORD-1004 | confirmed |
| `b2000000-0000-4000-8000-000000000005` | ORD-1005 | pending |
| `b2000000-0000-4000-8000-000000000006` | ORD-1006 | cancelled |
| `b2000000-0000-4000-8000-000000000007` | ORD-1007 | shipped |
| `b2000000-0000-4000-8000-000000000008` | ORD-1008 | delivered |
| `b2000000-0000-4000-8000-000000000009` | ORD-1009 | processing |
| `b2000000-0000-4000-8000-000000000010` | ORD-1010 | pending |

## Tests

```bash
python manage.py test -v 2
```

The suite covers existing and unknown products and orders, malformed IDs, missing, wrong, and malformed credentials, rejected `POST` requests, JSON 404s, inactive and out-of-stock products, and the seed command. GitHub Actions runs it on every push.

Results from real runs are recorded in [TEST_RESULTS.md](TEST_RESULTS.md).

## Deployment

This runs on a single Ubuntu VPS. Caddy terminates HTTPS and proxies requests to Gunicorn, which listens only on `127.0.0.1:8000`. The files referenced below are in [`deploy/`](deploy/).

```bash
# 1. System user, code, and persistent data directory
sudo adduser --system --group --no-create-home store-api
sudo git clone https://github.com/Khalidd3v/agentplace-store-api.git /srv/store-api
sudo python3.13 -m venv /srv/store-api/.venv
sudo /srv/store-api/.venv/bin/pip install -r /srv/store-api/requirements.txt
sudo install -d -o store-api -g store-api -m 750 /var/lib/store-api

# 2. Secrets, readable only by root and the service user
sudo install -d -m 750 -g store-api /etc/store-api
sudo tee /etc/store-api/env > /dev/null <<'EOF'
DJANGO_SECRET_KEY=<long random value>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=api.example.com
STORE_API_TOKEN=<long random value>
SQLITE_PATH=/var/lib/store-api/db.sqlite3
EOF
sudo chmod 640 /etc/store-api/env && sudo chgrp store-api /etc/store-api/env

# 3. Gunicorn under systemd (runs migrations on each start)
sudo cp /srv/store-api/deploy/store-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now store-api
sudo -u store-api bash -c 'set -a; . /etc/store-api/env; cd /srv/store-api && .venv/bin/python manage.py seed_store'

# 4. Caddy for HTTPS (edit the hostname first)
sudo cp /srv/store-api/deploy/Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy

# 5. Firewall: SSH and HTTP/HTTPS only
sudo ufw allow OpenSSH && sudo ufw allow 80,443/tcp && sudo ufw enable
```

Notes:

- The SQLite database is kept in `/var/lib/store-api`, outside the repository. Back it up with `sqlite3 /var/lib/store-api/db.sqlite3 ".backup '/path/to/backup.sqlite3'"`.
- Run one application instance. SQLite suits this small, read-mostly dataset, but not workloads with many concurrent writes.
- With `DJANGO_DEBUG=False`, Django trusts Caddy's `X-Forwarded-Proto` header and sends HSTS and `nosniff` headers. Caddy redirects HTTP to HTTPS.
- Gunicorn's access log records the method, path, and status code. It does not record the `Authorization` header.

## Agentplace setup

The agent is a store-support agent on the free Luna model. It has two API-backed actions:

| Action | Input | Request |
| --- | --- | --- |
| `check_product_stock` | `product_id` (UUID string) | `GET https://<host>/api/products/{product_id}/stock/` |
| `check_order_status` | `order_id` (UUID string) | `GET https://<host>/api/orders/{order_id}/status/` |

Both actions send `Authorization: Bearer <token>`. Store the token as a secret in the action's connection settings. Never put it in the agent's instructions, conversation text, screenshots, or this repository.

Suggested agent instructions:

> You are a store support assistant. You can check product stock and order status.
> - If the customer has not given a product ID or order ID, ask for it.
> - Always call `check_product_stock` or `check_order_status` to answer. Never guess stock levels or order statuses.
> - Base your answer only on the API result. If the item is not found, say so plainly and do not invent details.
> - If the ID is not valid, explain that it should look like `a1000000-0000-4000-8000-000000000001`.
> - If the service refuses the request or is unavailable, say you cannot retrieve the information right now. Do not claim success.
> - Never reveal credentials, internal errors, or technical details of the API.

## Project layout

```text
agentplace-store-api/
├── config/                 Django settings, URLs, WSGI
├── store/
│   ├── authentication.py   Bearer-token authentication
│   ├── exceptions.py       Error codes and the JSON error handler
│   ├── models.py           Product, Order, OrderItem
│   ├── views.py            The two endpoints
│   ├── management/commands/seed_store.py
│   └── tests/test_api.py
├── deploy/                 systemd unit and Caddyfile
├── requirements.txt
├── .env.example
├── TEST_RESULTS.md
└── AGENTPLACE_PROJECT_SPEC.md
```
