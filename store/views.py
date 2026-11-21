import uuid

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .exceptions import error_response
from .models import Order, Product
from .serializers import OrderStatusSerializer, ProductStockSerializer


def is_valid_uuid(value):
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def invalid_id_response():
    return error_response("INVALID_ID", "The ID must be a valid UUID.", status.HTTP_400_BAD_REQUEST)


class ProductStockView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        if not is_valid_uuid(product_id):
            return invalid_id_response()

        product = Product.objects.filter(pk=product_id).first()
        if product is None:
            return error_response("PRODUCT_NOT_FOUND", "Product was not found.", status.HTTP_404_NOT_FOUND)

        return Response({"success": True, "data": ProductStockSerializer(product).data})


class OrderStatusView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        if not is_valid_uuid(order_id):
            return invalid_id_response()

        order = Order.objects.filter(pk=order_id).first()
        if order is None:
            return error_response("ORDER_NOT_FOUND", "Order was not found.", status.HTTP_404_NOT_FOUND)

        return Response({"success": True, "data": OrderStatusSerializer(order).data})
