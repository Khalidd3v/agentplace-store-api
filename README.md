# Agentplace Store API

A small, read-only Django REST API for checking product stock and order status. An [Agentplace](https://agentplace.io) store agent running on the free Luna model calls it. It was built for the [Agentplace Backend Engineer assessment](https://agentplace.io/careers/backend-engineer).

**Stack:** Python 3.13, Django 5.2, Django REST Framework, SQLite, Gunicorn, Caddy.

## Project structure

```text
agentplace-store-api/
├── core/                   Django project: settings, urls, wsgi, asgi
├── store/                  Django app
│   ├── models.py           Product, Order, OrderItem
│   ├── serializers.py      Response serializers
│   ├── views.py            APIView classes with token authentication
│   ├── exceptions.py       JSON error format
│   ├── urls.py
│   ├── tests.py
│   └── management/commands/seed_store.py
├── manage.py
├── requirements.txt
├── .env.example
└── TEST_RESULTS.md
```

## Local setup

```bash
git clone https://github.com/Khalidd3v/agentplace-store-api.git
cd agentplace-store-api

python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env              # then set DJANGO_SECRET_KEY

python manage.py migrate
python manage.py seed_store       # 10 products, 10 orders, and the "agentplace" API user
python manage.py drf_create_token agentplace   # prints the API token
python manage.py runserver
```

| Variable | Description |
| --- | --- |
| `DJANGO_SECRET_KEY` | Required. |
| `DJANGO_DEBUG` | `True` for local development. Defaults to `False`. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames. |
| `SQLITE_PATH` | Optional database path. Defaults to `./db.sqlite3`. |

## Authentication

The API uses DRF's `TokenAuthentication` with the `Bearer` keyword. Each view sets the `IsAuthenticated` permission. Tokens live in the database and belong to the `agentplace` user.

```http
Authorization: Bearer <token>
```

- Create or show the token: `python manage.py drf_create_token agentplace`
- Rotate the token: `python manage.py drf_create_token -r agentplace`

## API

### `GET /api/products/{product_id}/stock/`

```bash
curl -H "Authorization: Bearer $TOKEN" \
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

Inactive products always report `stock_quantity: 0` and `in_stock: false`.

### `GET /api/orders/{order_id}/status/`

```bash
curl -H "Authorization: Bearer $TOKEN" \
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

The response does not include customer details.

### Errors

```json
{ "success": false, "error": { "code": "PRODUCT_NOT_FOUND", "message": "Product was not found." } }
```

| Situation | HTTP | Code |
| --- | --- | --- |
| Missing or invalid token | 401 | `UNAUTHORIZED` |
| ID is not a valid UUID | 400 | `INVALID_ID` |
| Product does not exist | 404 | `PRODUCT_NOT_FOUND` |
| Order does not exist | 404 | `ORDER_NOT_FOUND` |
| Method other than GET | 405 | `METHOD_NOT_ALLOWED` |

### Sample data

`seed_store` creates records with fixed IDs. You can run it more than once without creating duplicates.

- **Products:** `a1000000-0000-4000-8000-000000000001` to `…000000000010`. `…0003` is out of stock and `…0009` is inactive.
- **Orders:** `b2000000-0000-4000-8000-000000000001` to `…000000000010`. Between them they cover every status: pending, confirmed, processing, shipped, delivered, and cancelled.

The full list is in [seed_store.py](store/management/commands/seed_store.py).

## Tests

```bash
python manage.py test
```

Results from real runs are in [TEST_RESULTS.md](TEST_RESULTS.md).

## Deployment

The API runs on an Ubuntu VPS. Gunicorn listens on `127.0.0.1:8000`, and Caddy serves HTTPS and proxies to it.

1. Install the app in `/srv/store-api` with a virtualenv in `.venv`. Create a `store-api` system user and a persistent data directory at `/var/lib/store-api`, owned by that user.
2. Put the settings in `/etc/store-api/env` and make the file readable only by root and `store-api` (`chmod 640`):

   ```ini
   DJANGO_SECRET_KEY=<long random value>
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=api.example.com
   SQLITE_PATH=/var/lib/store-api/db.sqlite3
   ```

3. Create `/etc/systemd/system/store-api.service`:

   ```ini
   [Unit]
   Description=Agentplace store API
   After=network.target

   [Service]
   User=store-api
   WorkingDirectory=/srv/store-api
   EnvironmentFile=/etc/store-api/env
   ExecStartPre=/srv/store-api/.venv/bin/python manage.py migrate --noinput
   ExecStart=/srv/store-api/.venv/bin/gunicorn core.wsgi:application --bind 127.0.0.1:8000 --workers 2
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

4. Create `/etc/caddy/Caddyfile`. Caddy gets the TLS certificate and redirects HTTP to HTTPS on its own:

   ```caddyfile
   api.example.com {
       reverse_proxy 127.0.0.1:8000
   }
   ```

5. Start the service, seed the data, and create the token:

   ```bash
   sudo systemctl enable --now store-api
   sudo systemctl reload caddy
   sudo -u store-api bash -c 'set -a; . /etc/store-api/env; cd /srv/store-api && .venv/bin/python manage.py seed_store && .venv/bin/python manage.py drf_create_token agentplace'
   ```

6. Allow only SSH, HTTP, and HTTPS through the firewall: `sudo ufw allow OpenSSH && sudo ufw allow 80,443/tcp && sudo ufw enable`.

Keep `db.sqlite3` outside the repository and back it up. Run a single app instance, because SQLite is not built for many concurrent writers.

## Agentplace setup

Build a store-support agent on the free Luna model with two API actions:

| Action | Input | Request |
| --- | --- | --- |
| `check_product_stock` | `product_id` | `GET https://<host>/api/products/{product_id}/stock/` |
| `check_order_status` | `order_id` | `GET https://<host>/api/orders/{order_id}/status/` |

Store the token as a secret in the action's connection settings as `Authorization: Bearer <token>`. Never put it in the agent's instructions.

Suggested agent instructions:

> You are a store support assistant. You can check product stock and order status.
> If the customer has not given a product or order ID, ask for it.
> Always call the API to answer. Never guess stock levels or order statuses.
> If an item is not found, say so plainly. If the ID is invalid, ask for a valid one.
> If the API refuses the request or is unavailable, say you cannot get the information right now.
> Never reveal credentials or technical error details.
