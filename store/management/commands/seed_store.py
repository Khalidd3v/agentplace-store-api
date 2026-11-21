"""Load the 10 sample products and 10 sample orders.

IDs are fixed so the records can be referenced in tests and agent conversations.
Running the command again updates the same records instead of duplicating them.
"""

from datetime import datetime, timezone
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from store.models import Order, OrderItem, Product

# (id, sku, name, description, stock_quantity, is_active)
PRODUCTS = [
    ("a1000000-0000-4000-8000-000000000001", "SKU-1001", "Wireless Mouse", "2.4 GHz ergonomic mouse.", 25, True),
    ("a1000000-0000-4000-8000-000000000002", "SKU-1002", "Mechanical Keyboard", "Tenkeyless, brown switches.", 12, True),
    ("a1000000-0000-4000-8000-000000000003", "SKU-1003", "USB-C Hub", "7-in-1 hub with HDMI and card reader.", 0, True),
    ("a1000000-0000-4000-8000-000000000004", "SKU-1004", "27-inch Monitor", "1440p IPS display.", 7, True),
    ("a1000000-0000-4000-8000-000000000005", "SKU-1005", "Laptop Stand", "Adjustable aluminium stand.", 40, True),
    ("a1000000-0000-4000-8000-000000000006", "SKU-1006", "HD Webcam", "1080p webcam with microphone.", 15, True),
    ("a1000000-0000-4000-8000-000000000007", "SKU-1007", "Noise-Cancelling Headphones", "Over-ear, Bluetooth.", 3, True),
    ("a1000000-0000-4000-8000-000000000008", "SKU-1008", "1TB External SSD", "USB 3.2 portable drive.", 18, True),
    ("a1000000-0000-4000-8000-000000000009", "SKU-1009", "LED Desk Lamp", "Discontinued model.", 9, False),
    ("a1000000-0000-4000-8000-000000000010", "SKU-1010", "HDMI Cable 2m", "High-speed HDMI 2.1 cable.", 60, True),
]

# (id, order_number, customer_name, status, created_at, [(product_sku, quantity, unit_price)])
ORDERS = [
    ("b2000000-0000-4000-8000-000000000001", "ORD-1001", "Alice Johnson", "delivered", "2026-11-01T09:15:00", [("SKU-1001", 1, "24.99"), ("SKU-1010", 2, "9.99")]),
    ("b2000000-0000-4000-8000-000000000002", "ORD-1002", "Bob Smith", "shipped", "2026-11-10T14:30:00", [("SKU-1004", 1, "289.00")]),
    ("b2000000-0000-4000-8000-000000000003", "ORD-1003", "Carla Gomez", "processing", "2026-11-15T11:05:00", [("SKU-1002", 1, "89.50"), ("SKU-1001", 1, "24.99")]),
    ("b2000000-0000-4000-8000-000000000004", "ORD-1004", "David Lee", "confirmed", "2026-11-18T16:45:00", [("SKU-1007", 1, "199.00")]),
    ("b2000000-0000-4000-8000-000000000005", "ORD-1005", "Emma Brown", "pending", "2026-11-20T08:20:00", [("SKU-1005", 2, "39.00")]),
    ("b2000000-0000-4000-8000-000000000006", "ORD-1006", "Farid Khan", "cancelled", "2026-11-05T10:00:00", [("SKU-1003", 1, "49.99")]),
    ("b2000000-0000-4000-8000-000000000007", "ORD-1007", "Grace Kim", "shipped", "2026-11-12T13:10:00", [("SKU-1008", 1, "119.00"), ("SKU-1010", 1, "9.99")]),
    ("b2000000-0000-4000-8000-000000000008", "ORD-1008", "Hugo Martin", "delivered", "2026-10-28T17:55:00", [("SKU-1006", 1, "59.00")]),
    ("b2000000-0000-4000-8000-000000000009", "ORD-1009", "Isla Wilson", "processing", "2026-11-19T12:40:00", [("SKU-1002", 2, "89.50")]),
    ("b2000000-0000-4000-8000-000000000010", "ORD-1010", "Jamal Ahmed", "pending", "2026-11-21T07:30:00", [("SKU-1004", 1, "289.00"), ("SKU-1005", 1, "39.00")]),
]


class Command(BaseCommand):
    help = "Create or update the 10 sample products and 10 sample orders."

    @transaction.atomic
    def handle(self, *args, **options):
        products = {}
        for pk, sku, name, description, stock, active in PRODUCTS:
            product, _ = Product.objects.update_or_create(
                id=pk,
                defaults={
                    "sku": sku,
                    "name": name,
                    "description": description,
                    "stock_quantity": stock,
                    "is_active": active,
                },
            )
            products[sku] = product

        for pk, number, customer, status, created, items in ORDERS:
            order, _ = Order.objects.update_or_create(
                id=pk,
                defaults={
                    "order_number": number,
                    "customer_name": customer,
                    "status": status,
                    "created_at": datetime.fromisoformat(created).replace(tzinfo=timezone.utc),
                },
            )
            order.items.all().delete()
            OrderItem.objects.bulk_create(
                OrderItem(order=order, product=products[sku], quantity=qty, unit_price=Decimal(price))
                for sku, qty, price in items
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(PRODUCTS)} products and {len(ORDERS)} orders."))
