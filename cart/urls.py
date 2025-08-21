from django.urls import path

from .views import CartDetailView

urlpatterns = [
    path('', CartDetailView.as_view(), name='cart_detail'),
]
