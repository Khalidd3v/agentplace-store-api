from datetime import datetime, timedelta, timezone
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from .models import Order, OrderItem, Product

UNKNOWN_ID = "00000000-0000-4000-8000-000000000000"


class StoreAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="agentplace")
        cls.token = str(AccessToken.for_user(cls.user))

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

    def setUp(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def assertError(self, response, status_code, code):
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response.json()["success"], False)
        self.assertEqual(response.json()["error"]["code"], code)


class ProductStockTests(StoreAPITestCase):
    def test_existing_product_returns_stock(self):
        response = self.client.get(f"/api/products/{self.product.id}/stock/")
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
        data = self.client.get(f"/api/products/{self.empty_product.id}/stock/").json()["data"]
        self.assertEqual(data["stock_quantity"], 0)
        self.assertFalse(data["in_stock"])

    def test_inactive_product_is_not_reported_as_available(self):
        data = self.client.get(f"/api/products/{self.inactive_product.id}/stock/").json()["data"]
        self.assertEqual(data["stock_quantity"], 0)
        self.assertFalse(data["in_stock"])

    def test_unknown_product_returns_404(self):
        response = self.client.get(f"/api/products/{UNKNOWN_ID}/stock/")
        self.assertError(response, 404, "PRODUCT_NOT_FOUND")

    def test_invalid_product_id_returns_400(self):
        response = self.client.get("/api/products/not-a-uuid/stock/")
        self.assertError(response, 400, "INVALID_ID")


class OrderStatusTests(StoreAPITestCase):
    def test_existing_order_returns_status(self):
        response = self.client.get(f"/api/orders/{self.order.id}/status/")
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

    def test_order_response_has_no_customer_details(self):
        response = self.client.get(f"/api/orders/{self.order.id}/status/")
        self.assertNotIn("Alice", response.content.decode())

    def test_unknown_order_returns_404(self):
        response = self.client.get(f"/api/orders/{UNKNOWN_ID}/status/")
        self.assertError(response, 404, "ORDER_NOT_FOUND")

    def test_invalid_order_id_returns_400(self):
        response = self.client.get("/api/orders/12345/status/")
        self.assertError(response, 400, "INVALID_ID")


class AuthenticationTests(StoreAPITestCase):
    def setUp(self):
        self.url = f"/api/products/{self.product.id}/stock/"

    def test_missing_token_is_refused(self):
        response = self.client.get(self.url)
        self.assertError(response, 401, "UNAUTHORIZED")
        self.assertEqual(response.json()["error"]["message"], "Valid API credentials are required.")

    def test_wrong_token_is_refused(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer wrong-token")
        self.assertError(self.client.get(self.url), 401, "UNAUTHORIZED")

    def test_malformed_header_is_refused(self):
        for header in [self.token, f"Token {self.token}", "Bearer", f"Bearer {self.token} extra"]:
            with self.subTest(header=header):
                self.client.credentials(HTTP_AUTHORIZATION=header)
                self.assertError(self.client.get(self.url), 401, "UNAUTHORIZED")

    def test_token_in_query_string_is_refused(self):
        response = self.client.get(f"{self.url}?token={self.token}")
        self.assertError(response, 401, "UNAUTHORIZED")

    def test_expired_token_is_refused(self):
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=-timedelta(seconds=1))
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertError(self.client.get(self.url), 401, "UNAUTHORIZED")

    def test_inactive_user_is_refused(self):
        User.objects.filter(pk=self.user.pk).update(is_active=False)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertError(self.client.get(self.url), 401, "UNAUTHORIZED")


class MethodTests(StoreAPITestCase):
    def test_post_is_not_allowed(self):
        for url in [f"/api/products/{self.product.id}/stock/", f"/api/orders/{self.order.id}/status/"]:
            with self.subTest(url=url):
                self.assertError(self.client.post(url), 405, "METHOD_NOT_ALLOWED")


class ManagementCommandTests(APITestCase):
    def test_seed_is_idempotent(self):
        call_command("seed_store", stdout=StringIO())
        call_command("seed_store", stdout=StringIO())
        self.assertEqual(Product.objects.count(), 10)
        self.assertEqual(Order.objects.count(), 10)

    def test_create_agent_token_returns_working_30_day_token(self):
        out = StringIO()
        call_command("create_agent_token", stdout=out, stderr=StringIO())
        token = AccessToken(out.getvalue().strip())
        self.assertEqual(token["exp"] - token["iat"], 30 * 24 * 60 * 60)

        call_command("seed_store", stdout=StringIO())
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/products/a1000000-0000-4000-8000-000000000001/stock/")
        self.assertEqual(response.status_code, 200)
