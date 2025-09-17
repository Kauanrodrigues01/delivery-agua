from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.dashboard_view, name="dashboard"),
    path("products/", views.product_list, name="product_list"),
    path("products/create/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path(
        "products/<int:pk>/toggle-active/",
        views.product_toggle_active,
        name="product_toggle_active",
    ),
    # Category URLs
    path("categories/", views.category_list, name="category_list"),
    path("categories/create/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    # Order URLs
    path("orders/", views.order_list, name="order_list"),
    path("orders/create/", views.order_create, name="order_create"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/edit/", views.order_edit, name="order_edit"),
    path("orders/<int:pk>/cancel/", views.order_cancel, name="order_cancel"),
    path(
        "orders/<int:pk>/toggle-status/",
        views.order_toggle_status,
        name="order_toggle_status",
    ),
    path(
        "orders/<int:pk>/toggle-payment-status/",
        views.order_toggle_payment_status,
        name="order_toggle_payment_status",
    ),
    path(
        "orders/<int:pk>/cancel-payment/",
        views.order_cancel_payment,
        name="order_cancel_payment",
    ),
]
