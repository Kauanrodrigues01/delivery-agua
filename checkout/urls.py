from django.urls import path

from .views import (
    AwaitingPaymentView,
    CheckoutView,
    ErrorPaymentView,
    SuccessPaymentView,
    check_payment_status,
)

app_name = "checkout"

urlpatterns = [
    path("", CheckoutView.as_view(), name="checkout"),
    path(
        "aguardando-pagamento/<int:order_id>/",
        AwaitingPaymentView.as_view(),
        name="awaiting_payment",
    ),
    path(
        "pagamento-realizado/<int:order_id>/",
        SuccessPaymentView.as_view(),
        name="success_payment",
    ),
    path(
        "erro-pagamento/",
        ErrorPaymentView.as_view(),
        name="error_payment",
    ),
    path(
        "erro-pagamento/<int:order_id>/",
        ErrorPaymentView.as_view(),
        name="error_payment_with_order",
    ),
    path(
        "api/check-payment/<int:order_id>/",
        check_payment_status,
        name="check_payment_status",
    ),
]
