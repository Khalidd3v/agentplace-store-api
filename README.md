# Agentplace Store API

A small, read-only Django REST API for checking product stock and order status. An [Agentplace](https://agentplace.io) store agent running on the free Luna model calls it. It was built for the [Agentplace Backend Engineer assessment](https://agentplace.io/careers/backend-engineer).

**Stack:** Python 3.13, Django 5.2, Django REST Framework, Simple JWT, SQLite, Gunicorn, Docker, Caddy.

## Project structure

```text
agentplace-store-api/
├── core/                   Django project: settings, urls, wsgi, asgi
├── store/                  Django app
│   ├── models.py           Product, Order, OrderItem
│   ├── serializers.py      Response serializers
│   ├── views.py            APIView classes with JWT authentication
│   ├── exceptions.py       JSON error format
│   ├── urls.py
│   ├── tests.py
│   └── management/commands/
│       ├── seed_store.py           sample data
│       └── create_agent_token.py   JWT for the agent
├── deploy/docker/          Dockerfile and compose file for production
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
python manage.py seed_store           # 10 products and 10 orders
python manage.py create_agent_token   # prints a 30-day JWT for the agent
python manage.py runserver
```

| Variable | Description |
| --- | --- |
| `DJANGO_SECRET_KEY` | Required. Also signs the JWTs. |
| `DJANGO_DEBUG` | `True` for local development. Defaults to `False`. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames. |
| `SQLITE_PATH` | Optional database path. Defaults to `./db.sqlite3`. |

## Authentication

The API uses [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/). Each view sets `JWTAuthentication` and the `IsAuthenticated` permission. Access tokens last 30 days (`SIMPLE_JWT` in `core/settings.py`).

```http
Authorization: Bearer <token>
```

`python manage.py create_agent_token` prints a token for the `agentplace` user. It creates the user, with no password, if needed. There is no login endpoint, because the agent uses one fixed token stored as a secret.

- **Renew:** run the command again before the 30 days are up and update the secret in Agentplace.
- **Revoke every token:** deactivate the `agentplace` user, or change `DJANGO_SECRET_KEY`.

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
| Missing, invalid, or expired token | 401 | `UNAUTHORIZED` |
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

The API runs on an Ubuntu VPS in Docker. Gunicorn listens on port 8000 inside the container, and a Caddy container that already serves other sites on the same host handles HTTPS and proxies to it. The files are in [deploy/docker](deploy/docker).

| File | Purpose |
| --- | --- |
| `Dockerfile` | Python 3.13 image. Runs as a non-root user, applies migrations at start, then starts Gunicorn with 2 workers. |
| `compose.yaml` | One `api` service. It joins the Caddy stack's Docker network (`zmapos-backend_default`; change it to match yours) and publishes no host ports. SQLite lives in the `data` volume. |
| `Dockerfile.dockerignore` | Keeps `.git`, local databases and `deploy/docker/env` out of the image. |

1. Create `deploy/docker/env`. It is gitignored, so set `chmod 600` on it:

   ```ini
   DJANGO_SECRET_KEY=<long random value>
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=api.example.com,localhost,127.0.0.1,agentplace-store-api
   SQLITE_PATH=/data/db.sqlite3
   ```

2. Build and start the container, then seed the data and create the agent's token:

   ```bash
   cd deploy/docker
   docker compose up -d --build
   docker exec agentplace-store-api python manage.py seed_store
   docker exec agentplace-store-api python manage.py create_agent_token
   ```

3. Add a site block to the shared Caddyfile. Caddy gets the TLS certificate and redirects HTTP to HTTPS on its own:

   ```caddyfile
   api.example.com {
       encode gzip
       reverse_proxy agentplace-store-api:8000
   }
   ```

   Check the file with `caddy validate` before you apply it. If the Caddy admin API is off, you have to restart the Caddy container to load the change, and every site it serves is down for a few seconds. If the Caddyfile is bind-mounted as a single file, edit it in place (for example, by appending to it). Editors that replace the file break the mount.

4. To update, pull the new code and rebuild. Only this container is replaced, and the database volume is kept:

   ```bash
   git pull
   cd deploy/docker && docker compose up -d --build
   ```

To run the tests against the built image: `docker run --rm -e DJANGO_SECRET_KEY=test agentplace-store-api python manage.py test`.

Back up the `agentplace-store-api_data` volume. Run a single app instance, because SQLite is not built for many concurrent writers.

## Agentplace setup

Build a store-support agent on the free Luna model with two API actions:

| Action | Input | Request |
| --- | --- | --- |
| `check_product_stock` | `product_id` | `GET https://<host>/api/products/{product_id}/stock/` |
| `check_order_status` | `order_id` | `GET https://<host>/api/orders/{order_id}/status/` |

Store the token from `create_agent_token` as a secret in the action's connection settings, sent as `Authorization: Bearer <token>`. Never put it in the agent's instructions. Renew it every 30 days.

Suggested agent instructions:

> You are a store support assistant. You can check product stock and order status.
> If the customer has not given a product or order ID, ask for it.
> Always call the API to answer. Never guess stock levels or order statuses.
> If an item is not found, say so plainly. If the ID is invalid, ask for a valid one.
> If the API refuses the request or is unavailable, say you cannot get the information right now.
> Never reveal credentials or technical error details.
