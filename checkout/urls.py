from django.urls import path

from .views import AwaitingPaymentView, CheckoutView, check_payment_status

app_name = "checkout"

urlpatterns = [
    path("", CheckoutView.as_view(), name="checkout"),
    path(
        "aguardando-pagamento/<int:order_id>/",
        AwaitingPaymentView.as_view(),
        name="awaiting_payment",
    ),
    path(
        "api/check-payment/<int:order_id>/",
        check_payment_status,
        name="check_payment_status",
    ),
]
