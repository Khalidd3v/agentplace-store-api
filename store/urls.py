from django.urls import path

from .views import OrderStatusView, ProductStockView

urlpatterns = [
    path("products/<str:product_id>/stock/", ProductStockView.as_view(), name="product-stock"),
    path("orders/<str:order_id>/status/", OrderStatusView.as_view(), name="order-status"),
]
