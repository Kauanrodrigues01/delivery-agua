from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('', views.dashboard_view, name='dashboard'),
    path('products/', views.product_list, name='dashboard_product_list'),
    path('products/create/', views.product_create, name='dashboard_product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='dashboard_product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='dashboard_product_delete'),
]