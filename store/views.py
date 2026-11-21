import uuid

from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .exceptions import InvalidId, OrderNotFound, ProductNotFound, error_body
from .models import Order, Product


def parse_uuid(value):
    try:
        return uuid.UUID(value)
    except ValueError:
        raise InvalidId()


@api_view(["GET"])
def product_stock(request, product_id):
    product = Product.objects.filter(pk=parse_uuid(product_id)).first()
    if product is None:
        raise ProductNotFound()

    quantity = product.available_quantity
    return Response(
        {
            "success": True,
            "data": {
                "product_id": str(product.id),
                "sku": product.sku,
                "name": product.name,
                "stock_quantity": quantity,
                "in_stock": quantity > 0,
            },
        }
    )


@api_view(["GET"])
def order_status(request, order_id):
    order = Order.objects.filter(pk=parse_uuid(order_id)).first()
    if order is None:
        raise OrderNotFound()

    return Response(
        {
            "success": True,
            "data": {
                "order_id": str(order.id),
                "order_number": order.order_number,
                "status": order.status,
                "created_at": order.created_at.isoformat().replace("+00:00", "Z"),
            },
        }
    )


def json_not_found(request, exception):
    return JsonResponse(error_body("NOT_FOUND", "The requested resource was not found."), status=404)


def json_server_error(request):
    return JsonResponse(error_body("SERVER_ERROR", "An unexpected error occurred."), status=500)
