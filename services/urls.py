from django.urls import path

from . import views

app_name = 'services'

urlpatterns = [
    path('webhook/mercadopago/', views.webhook_mercadopago, name='webhook_mercadopago'),
]
