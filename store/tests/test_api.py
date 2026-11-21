from datetime import datetime, timezone
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings

from store.models import Order, OrderItem, Product

TOKEN = "test-token-123"
UNKNOWN_ID = "00000000-0000-4000-8000-000000000000"


@override_settings(STORE_API_TOKEN=TOKEN)
class ApiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(sku="SKU-1", name="Wireless Mouse", stock_quantity=25)
        cls.empty_product = Product.objects.create(sku="SKU-2", name="USB-C Hub", stock_quantity=0)
        cls.inactive_product = Product.objects.create(
            sku="SKU-3", name="Desk Lamp", stock_quantity=9, is_active=False
        )
        cls.order = Order.objects.create(
            order_number="ORD-1",
            customer_name="Alice Johnson",
            status=Order.Status.SHIPPED,
            created_at=datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc),
        )
        OrderItem.objects.create(order=cls.order, product=cls.product, quantity=1, unit_price="24.99")

    def get(self, url, token=TOKEN, **headers):
        if token is not None:
            headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return self.client.get(url, **headers)

    def assert_error(self, response, status, code):
        self.assertEqual(response.status_code, status)
        body = response.json()
        self.assertIs(body["success"], False)
        self.assertEqual(body["error"]["code"], code)
        self.assertTrue(body["error"]["message"])


class ProductStockTests(ApiTestCase):
    def url(self, product_id):
        return f"/api/products/{product_id}/stock/"

    def test_existing_product_returns_stock(self):
        response = self.get(self.url(self.product.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "success": True,
                "data": {
                    "product_id": str(self.product.id),
                    "sku": "SKU-1",
                    "name": "Wireless Mouse",
                    "stock_quantity": 25,
                    "in_stock": True,
                },
            },
        )

    def test_product_with_zero_stock_is_not_in_stock(self):
        data = self.get(self.url(self.empty_product.id)).json()["data"]
        self.assertEqual(data["stock_quantity"], 0)
        self.assertIs(data["in_stock"], False)

    def test_inactive_product_is_not_reported_as_available(self):
        data = self.get(self.url(self.inactive_product.id)).json()["data"]
        self.assertEqual(data["stock_quantity"], 0)
        self.assertIs(data["in_stock"], False)

    def test_unknown_product_returns_404(self):
        self.assert_error(self.get(self.url(UNKNOWN_ID)), 404, "PRODUCT_NOT_FOUND")

    def test_malformed_id_returns_400(self):
        self.assert_error(self.get(self.url("not-a-uuid")), 400, "INVALID_ID")


class OrderStatusTests(ApiTestCase):
    def url(self, order_id):
        return f"/api/orders/{order_id}/status/"

    def test_existing_order_returns_status(self):
        response = self.get(self.url(self.order.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "success": True,
                "data": {
                    "order_id": str(self.order.id),
                    "order_number": "ORD-1",
                    "status": "shipped",
                    "created_at": "2026-11-21T10:00:00Z",
                },
            },
        )

    def test_order_response_excludes_customer_details(self):
        response = self.get(self.url(self.order.id))
        self.assertNotIn("Alice", response.content.decode())

    def test_unknown_order_returns_404(self):
        self.assert_error(self.get(self.url(UNKNOWN_ID)), 404, "ORDER_NOT_FOUND")

    def test_malformed_id_returns_400(self):
        self.assert_error(self.get(self.url("12345")), 400, "INVALID_ID")


class AuthorizationTests(ApiTestCase):
    def setUp(self):
        self.url = f"/api/products/{self.product.id}/stock/"

    def test_missing_token_is_refused(self):
        response = self.get(self.url, token=None)
        self.assert_error(response, 401, "UNAUTHORIZED")
        self.assertEqual(response.json()["error"]["message"], "Valid API credentials are required.")
        self.assertEqual(response["WWW-Authenticate"], "Bearer")

    def test_wrong_token_is_refused(self):
        self.assert_error(self.get(self.url, token="wrong-token"), 401, "UNAUTHORIZED")

    def test_malformed_header_is_refused(self):
        for header in [TOKEN, f"Token {TOKEN}", "Bearer", f"Bearer {TOKEN} extra"]:
            with self.subTest(header=header):
                response = self.client.get(self.url, HTTP_AUTHORIZATION=header)
                self.assert_error(response, 401, "UNAUTHORIZED")

    def test_token_in_query_string_is_refused(self):
        response = self.client.get(f"{self.url}?token={TOKEN}")
        self.assert_error(response, 401, "UNAUTHORIZED")

    def test_auth_is_checked_before_id_validation(self):
        response = self.get("/api/orders/not-a-uuid/status/", token=None)
        self.assert_error(response, 401, "UNAUTHORIZED")

    @override_settings(STORE_API_TOKEN="")
    def test_unconfigured_token_refuses_everything(self):
        self.assert_error(self.get(self.url, token=""), 401, "UNAUTHORIZED")
        self.assert_error(self.get(self.url, token="anything"), 401, "UNAUTHORIZED")


class MethodAndRoutingTests(ApiTestCase):
    def test_post_is_not_allowed(self):
        for url in [f"/api/products/{self.product.id}/stock/", f"/api/orders/{self.order.id}/status/"]:
            with self.subTest(url=url):
                response = self.client.post(url, HTTP_AUTHORIZATION=f"Bearer {TOKEN}")
                self.assert_error(response, 405, "METHOD_NOT_ALLOWED")

    def test_post_without_token_is_refused(self):
        response = self.client.post(f"/api/products/{self.product.id}/stock/")
        self.assert_error(response, 401, "UNAUTHORIZED")

    def test_unknown_route_returns_json_404(self):
        self.assert_error(self.get("/api/nothing-here/"), 404, "NOT_FOUND")


class SeedCommandTests(TestCase):
    def test_seed_creates_ten_products_and_orders_idempotently(self):
        for _ in range(2):
            call_command("seed_store", stdout=StringIO())
        self.assertEqual(Product.objects.count(), 10)
        self.assertEqual(Order.objects.count(), 10)
        self.assertTrue(all(order.items.exists() for order in Order.objects.all()))
