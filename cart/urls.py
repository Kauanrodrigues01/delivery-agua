from django.urls import path

from .views import (
    AddToCartView,
    CartDetailView,
    decrease_cart_item,
    increase_cart_item,
    remove_cart_item,
)

urlpatterns = [
    path("", CartDetailView.as_view(), name="cart_detail"),
    path("add/", AddToCartView.as_view(), name="add_to_cart"),
    path("increase/", increase_cart_item, name="increase_cart_item"),
    path("decrease/", decrease_cart_item, name="decrease_cart_item"),
    path("remove/", remove_cart_item, name="remove_cart_item"),
]
