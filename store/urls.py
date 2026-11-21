from django.urls import path

from . import views

urlpatterns = [
    path("products/<str:product_id>/stock/", views.product_stock, name="product-stock"),
    path("orders/<str:order_id>/status/", views.order_status, name="order-status"),
]
