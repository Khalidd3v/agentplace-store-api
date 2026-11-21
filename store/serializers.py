from rest_framework import serializers

from .models import Order, Product


class ProductStockSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(source="id")
    stock_quantity = serializers.IntegerField(source="available_quantity")
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["product_id", "sku", "name", "stock_quantity", "in_stock"]

    def get_in_stock(self, product):
        return product.available_quantity > 0


class OrderStatusSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source="id")

    class Meta:
        model = Order
        fields = ["order_id", "order_number", "status", "created_at"]
