from django.urls import path

from .views import AddToCartView, CartDetailView

urlpatterns = [
    path('', CartDetailView.as_view(), name='cart_detail'),
    path('add/', AddToCartView.as_view(), name='add_to_cart'),
]
