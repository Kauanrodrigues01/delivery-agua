from django.urls import path

from .views import ProductListView, add_to_cart

urlpatterns = [
    path("", ProductListView.as_view(), name="product_list"),
    path("add-to-cart/<int:product_id>/", add_to_cart, name="add_to_cart_func"),
]
